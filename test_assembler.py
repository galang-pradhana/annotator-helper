import sys
from prompt_assembler import assemble_evaluator_prompt, LANGUAGE_MAP

def test_prompt_assembler():
    print("Testing assemble_evaluator_prompt...")
    try:
        # Test PR task
        prompt_pr = assemble_evaluator_prompt("ID", "PR")
        print(f"✅ PR Prompt assembled successfully. Length: {len(prompt_pr)} chars.")
        if "BLOCK A" not in prompt_pr:
            print("❌ BLOCK A is missing from PR prompt.")
            return False
            
        # Test AFM task
        prompt_afm = assemble_evaluator_prompt("JA", "AFM")
        print(f"✅ AFM Prompt assembled successfully. Length: {len(prompt_afm)} chars.")
        if "BLOCK D — OUTPUT CONTRACT" not in prompt_afm:
            print("❌ BLOCK D is missing from AFM prompt.")
            return False
            
        print("🎉 All tests passed!")
        return True
    except Exception as e:
        print(f"❌ Error during assembly: {e}")
        return False

if __name__ == "__main__":
    success = test_prompt_assembler()
    if not success:
        sys.exit(1)
