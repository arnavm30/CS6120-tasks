#include "llvm/Pass.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Function.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Transforms/Utils/LoopUtils.h"
#include "llvm/Transforms/Utils/Mem2Reg.h"
#include "llvm/Transforms/Utils/LoopSimplify.h"
#include <list>

using namespace llvm;

namespace {
    struct LICMPass : public PassInfoMixin<LICMPass> {
    public:
        PreservedAnalyses run(Loop &L, LoopAnalysisManager &LAM,
                              LoopStandardAnalysisResults &AR, LPMUpdater &U) {

            DominatorTree &DT = AR.DT;
            auto *preheader = L.getLoopPreheader();

            std::list<Instruction *> loopInvInstrs;
            bool changed = true;

            while (changed) {
                changed = false;
                for (auto *BB : L.blocks()) {
                    for (auto &I : *BB) {
                        if (I.isTerminator())
                            continue;
                        if (isa<PHINode>(I))
                            continue;
                        if (std::find(loopInvInstrs.begin(), loopInvInstrs.end(), &I) != loopInvInstrs.end())
                            continue;

                        bool isLI = true;
                        for (auto &Op : I.operands()) {
                            auto *OpInst = dyn_cast<Instruction>(Op);
                            if (!OpInst)
                                continue;

                            bool AllDefsOutside = !L.contains(OpInst);
                            bool OneDefAndLI = L.contains(OpInst) &&
                                std::find(loopInvInstrs.begin(), loopInvInstrs.end(), OpInst) != loopInvInstrs.end();

                            if (!AllDefsOutside && !OneDefAndLI) {
                                isLI = false;
                                break;
                            }
                        }

                        if (isLI) {
                            errs() << "Marked loop-invariant: " << I << "\n";
                            loopInvInstrs.push_back(&I);
                            changed = true;
                        }
                    }
                }
            }

            std::list<Instruction *> toMove;
            for (auto *I : loopInvInstrs) {
                if (isSafeToMove(I, L, DT)) {
                    toMove.push_back(I);
                }
            }

            for (auto *I : toMove) {
                I->moveBefore(preheader->getTerminator());
                errs() << "Moved to preheader: " << *I << "\n";
            }

            return toMove.empty() ? PreservedAnalyses::all() : PreservedAnalyses::none();
        }

    private:
        bool isSafeToMove(Instruction *I, Loop &L, DominatorTree &DT) {
            for (auto &U : I->uses()) {
                auto *User = dyn_cast<Instruction>(U.getUser());
                if (!User || !DT.dominates(I, User))
                    return false;
            }

            SmallVector<BasicBlock *, 4> ExitBlocks;
            L.getExitBlocks(ExitBlocks);
            for (auto *Exit : ExitBlocks) {
                if (!DT.dominates(I->getParent(), Exit)) {
                    return isDeadAfterLoop(I, L) && !mayHaveSideEffects(I);
                }
            }

            return true;
        }

        bool isDeadAfterLoop(Instruction *I, Loop &L) {
            for (auto &U : I->uses()) {
                auto *User = dyn_cast<Instruction>(U.getUser());
                if (User && !L.contains(User->getParent()))
                    return false;
            }
            return true;
        }

        bool mayHaveSideEffects(Instruction *I) {
            return I->mayWriteToMemory() || I->mayThrow();
        }
    };
}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo 
llvmGetPassPluginInfo() {
    return {
        LLVM_PLUGIN_API_VERSION, 
        "LICM", 
        "v0.1",
        [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, FunctionPassManager &FPM,
                ArrayRef<PassBuilder::PipelineElement>) {
                    if (Name == "my-licm") {
                        FPM.addPass(PromotePass());
                        FPM.addPass(LoopSimplifyPass());
                        FPM.addPass(createFunctionToLoopPassAdaptor(LICMPass()));
                        return true;
                    }
                    return false;
                });
        }
    };
}
