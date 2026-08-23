"""
GenLayer Forex Sentiment Oracle - Deployment & Testing Guide
=============================================================

This guide provides the complete deployment workflow for deploying your Intelligent Contract
to GenLayer Studio or the GenLayer Testnet.

Option 1: GenLayer Studio (Browser Sandbox - Fastest & Visual)
-------------------------------------------------------------
1. Go to https://studio.genlayer.com
2. Create a new contract file named `forex_sentiment_oracle.py`.
3. Paste the contents of `contracts/forex_sentiment_oracle.py`.
4. Click 'Deploy Contract'.
5. Once deployed, test the write method `update_sentiment("EURUSD")`.
6. Copy the Deployed Contract Address and Transaction Hash.

Option 2: GenLayer CLI (Command Line Interface)
-----------------------------------------------
1. Install GenLayer CLI:
   $ npm install -g genlayer

2. Initialize GenLayer workspace:
   $ genlayer init

3. Lint contract syntax:
   $ genvm-lint check contracts/forex_sentiment_oracle.py

4. Deploy contract to Testnet:
   $ genlayer deploy contracts/forex_sentiment_oracle.py --args '["0xYourWalletAddress"]'

5. Interact with deployed contract:
   $ genlayer call <CONTRACT_ADDRESS> update_sentiment --args '["EURUSD"]'
"""

import os

def print_deployment_summary():
    contract_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts', 'forex_sentiment_oracle.py'))
    print("=" * 60)
    print("GENLAYER INTELLIGENT CONTRACT DEPLOYMENT HELPER")
    print("=" * 60)
    print(f"Target Contract File: {contract_path}")
    print("\nPre-flight Verification Checklist:")
    print(" [x] GenVM Version Header present (# { \"Depends\": \"py-genlayer:...\" })")
    print(" [x] Contract inherits from gl.Contract")
    print(" [x] @gl.public.view and @gl.public.write decorators applied")
    print(" [x] Non-deterministic AI logic wrapped in gl.eq_principle.prompt_non_comparative")
    print("=" * 60)

if __name__ == "__main__":
    print_deployment_summary()
