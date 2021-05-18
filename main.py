from mathvault import MathVault

if __name__ == "__main__":
    obsidian_vault = r"C:\Users\james\Documents\Math"
    sm_collection = r"C:\SuperMemo\systems\Testing"
    mv = MathVault(obsidian_vault, sm_collection)
    mv.regenerate_cards()

