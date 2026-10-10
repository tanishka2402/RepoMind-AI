import { ethers } from "ethers";
import fs from "node:fs";
import path from "node:path";

const RPC_URL = "http://127.0.0.1:8545";

async function main() {
  const provider = new ethers.JsonRpcProvider(RPC_URL);

  const accounts = await provider.listAccounts();

  if (accounts.length === 0) {
    throw new Error("No accounts available on the local blockchain.");
  }

  const deployer = accounts[0];

  console.log("Deploying from:", deployer.address);

  const artifactPath = path.join(
    process.cwd(),
    "artifacts",
    "contracts",
    "RepoMindRegistry.sol",
    "RepoMindRegistry.json",
  );

  const artifact = JSON.parse(
    fs.readFileSync(artifactPath, "utf8"),
  );

  const signer = await provider.getSigner(deployer.address);

  const factory = new ethers.ContractFactory(
    artifact.abi,
    artifact.bytecode,
    signer,
  );

  const contract = await factory.deploy();

  await contract.waitForDeployment();

  const address = await contract.getAddress();

  console.log("RepoMindRegistry deployed at:");
  console.log(address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
