#include "llvm/Pass.h"
#include "llvm/IR/Module.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"

using namespace llvm;

bool isPowerOfTwoConstant(Value *v, unsigned &shiftAmount) {
    if (auto *C = dyn_cast<ConstantInt>(v)) {
        uint64_t val = C->getZExtValue();
        if (isPowerOf2_64(val)) {
            shiftAmount = Log2_64(val);
            return true;
        }
    }
    return false;
}

namespace {

struct SkeletonPass : public PassInfoMixin<SkeletonPass> {
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM) {
        bool modified = false;
        for (auto &F : M.functions()) {
            for (auto &B : F) {
                for (auto I = B.begin(); I != B.end();) { 
                    Instruction *inst = &(*I++);
                    
                    if (auto *op = dyn_cast<BinaryOperator>(inst)) {
                        IRBuilder<> builder(op);
                        Value *lhs = op->getOperand(0);
                        Value *rhs = op->getOperand(1);
                        unsigned shiftAmount = 0;

                        Instruction *newInst = nullptr; // Placeholder for replacement

                        // Replace x * 2^n (or 2^n * x) with x << n
                        if (op->getOpcode() == Instruction::Mul) {
                            if (isPowerOfTwoConstant(rhs, shiftAmount)) {
                                newInst = BinaryOperator::CreateShl(lhs, 
                                    ConstantInt::get(rhs->getType(), shiftAmount));
                            } else if (isPowerOfTwoConstant(lhs, shiftAmount)) {
                                newInst = BinaryOperator::CreateShl(rhs, 
                                    ConstantInt::get(lhs->getType(), shiftAmount));
                            }
                        }

                        // Replace x / 2^n with x >> n
                        else if (isPowerOfTwoConstant(rhs, shiftAmount)) {
                            if (op->getOpcode() == Instruction::UDiv) {
                                newInst = BinaryOperator::CreateLShr(lhs, 
                                    ConstantInt::get(rhs->getType(), shiftAmount));
                            } else if (op->getOpcode() == Instruction::SDiv) {
                                newInst = BinaryOperator::CreateAShr(lhs, 
                                    ConstantInt::get(rhs->getType(), shiftAmount));
                            }
                        }

                        // Replace instruction if we created a new one
                        if (newInst) {
                            newInst->insertAfter(op);
                            op->replaceAllUsesWith(newInst);
                            op->eraseFromParent();
                            modified = true;
                        }
                    }
                }
            }
        }
        return modified ? PreservedAnalyses::none() : PreservedAnalyses::all();
    }
};

} 

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo 
llvmGetPassPluginInfo() {
    return {
        .APIVersion = LLVM_PLUGIN_API_VERSION,
        .PluginName = "Skeleton pass",
        .PluginVersion = "v0.1",
        .RegisterPassBuilderCallbacks = [](PassBuilder &PB) {
            PB.registerPipelineStartEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel Level) {
                    MPM.addPass(StrengthReductionPass());
                });
        }
    };
}
