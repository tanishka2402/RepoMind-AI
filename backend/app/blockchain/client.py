"""
Ethereum client for RepoMind-AI blockchain integration.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

from web3 import Web3


DEFAULT_RPC_URL = "http://127.0.0.1:8545"

DEFAULT_CONTRACT_ADDRESS = (
    "0x5FbDB2315678afecb367f032d93F642f64180aa3"
)


class BlockchainClient:
    """Client for interacting with RepoMindRegistry."""

    def __init__(
        self,
        rpc_url: str | None = None,
        contract_address: str | None = None,
        private_key: str | None = None,
    ):
        self.rpc_url = (
            rpc_url
            or os.getenv(
                "REPOMIND_BLOCKCHAIN_RPC_URL",
                DEFAULT_RPC_URL,
            )
        )

        self.contract_address = (
            contract_address
            or os.getenv(
                "REPOMIND_CONTRACT_ADDRESS",
                DEFAULT_CONTRACT_ADDRESS,
            )
        )

        self.private_key = (
            private_key
            or os.getenv(
                "REPOMIND_BLOCKCHAIN_PRIVATE_KEY"
            )
        )

        self.web3 = Web3(
            Web3.HTTPProvider(self.rpc_url)
        )

        if not self.web3.is_connected():
            raise RuntimeError(
                "Unable to connect to blockchain RPC: "
                f"{self.rpc_url}"
            )

        if not self.private_key:
            raise RuntimeError(
                "REPOMIND_BLOCKCHAIN_PRIVATE_KEY "
                "is not configured."
            )

        self.account = (
            self.web3.eth.account.from_key(
                self.private_key
            )
        )

        abi_path = (
            Path(__file__).resolve()
            .parents[3]
            / "blockchain"
            / "blockchain"
            / "artifacts"
            / "contracts"
            / "RepoMindRegistry.sol"
            / "RepoMindRegistry.json"
        )

        if not abi_path.exists():
            raise FileNotFoundError(
                "RepoMindRegistry artifact not found: "
                f"{abi_path}"
            )

        with abi_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            artifact = json.load(file)

        self.contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(
                self.contract_address
            ),
            abi=artifact["abi"],
        )

    def register_analysis(
        self,
        analysis_id: int,
        repository_hash: str,
        report_hash: str,
        summary_report: str,
    ) -> Dict[str, Any]:
        """Register a RepoMind analysis on-chain."""

        repository_hash_bytes = bytes.fromhex(
            repository_hash
        )

        report_hash_bytes = bytes.fromhex(
            report_hash
        )

        nonce = self.web3.eth.get_transaction_count(
            self.account.address
        )

        transaction = (
            self.contract.functions.registerAnalysis(
                analysis_id,
                repository_hash_bytes,
                report_hash_bytes,
                summary_report,
            )
            .build_transaction(
                {
                    "from": self.account.address,
                    "nonce": nonce,
                    "chainId": self.web3.eth.chain_id,
                    "gas": 500_000,
                    "gasPrice": self.web3.eth.gas_price,
                }
            )
        )

        signed_transaction = (
            self.web3.eth.account.sign_transaction(
                transaction,
                private_key=self.private_key,
            )
        )

        transaction_hash = (
            self.web3.eth.send_raw_transaction(
                signed_transaction.raw_transaction
            )
        )

        receipt = (
            self.web3.eth.wait_for_transaction_receipt(
                transaction_hash
            )
        )

        return {
            "transaction_hash": (
                transaction_hash.hex()
            ),
            "block_number": receipt.blockNumber,
            "contract_address": self.contract_address,
            "submitted_by": self.account.address,
        }

    def get_analysis(
        self,
        analysis_id: int,
    ):
        """Retrieve an analysis from blockchain."""

        return self.contract.functions.getAnalysis(
            analysis_id
        ).call()

    def verify_report(
        self,
        analysis_id: int,
        report_hash: str,
    ) -> bool:
        """Verify a report hash against blockchain."""

        return self.contract.functions.verifyReport(
            analysis_id,
            bytes.fromhex(report_hash),
        ).call()
