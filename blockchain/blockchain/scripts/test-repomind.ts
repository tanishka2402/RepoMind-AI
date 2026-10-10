import { ethers } from "ethers";
import fs from "node:fs";
import path from "node:path";

const RPC_URL = "http://127.0.0.1:8545";

const CONTRACT_ADDRESS =
  "0x5FbDB2315678afecb367f032d93F642f64180aa3";

async function main() {
  const provider = new ethers.JsonRpcProvider(RPC_URL);

  const accounts = await provider.listAccounts();
  const signer = await provider.getSigner(accounts[0].address);

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

  const contract = new ethers.Contract(
    CONTRACT_ADDRESS,
    artifact.abi,
    signer,
  );

  let analysisId = 1;

while (await contract.exists(analysisId)) {
  analysisId++;
}

console.log("Using available analysis ID:", analysisId);

  const repository =
    "octocat/Hello-World";

  const summaryReport =
    "RepoMind-AI Analysis Summary: " +
    "Repository architecture, code quality, " +
    "documentation, security, risk, and " +
    "recommendations were analyzed.";

  const repositoryHash =
    ethers.keccak256(
      ethers.toUtf8Bytes(repository),
    );

  const reportHash =
    ethers.keccak256(
      ethers.toUtf8Bytes(summaryReport),
    );

  console.log("Registering analysis...");
  console.log("Analysis ID:", analysisId);
  console.log("Repository:", repository);
  console.log("Repository hash:", repositoryHash);
  console.log("Report hash:", reportHash);

  const tx = await contract.registerAnalysis(
    analysisId,
    repositoryHash,
    reportHash,
    summaryReport,
  );

  await tx.wait();

  console.log("\nAnalysis registered successfully.");
  console.log("Transaction:", tx.hash);

  const record =
    await contract.getAnalysis(analysisId);

  console.log("\nStored blockchain record:");
  console.log("Analysis ID:", record[0].toString());
  console.log("Repository hash:", record[1]);
  console.log("Report hash:", record[2]);
  console.log("Summary:", record[3]);
  console.log("Submitted by:", record[4]);
  console.log(
    "Timestamp:",
    record[5].toString(),
  );

  const verified =
    await contract.verifyReport(
      analysisId,
      reportHash,
    );

  console.log(
    "\nReport verification:",
    verified,
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
