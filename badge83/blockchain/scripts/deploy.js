const hre = require("hardhat");

async function main() {
  const Badge83Anchor = await hre.ethers.getContractFactory("Badge83Anchor");
  const anchor = await Badge83Anchor.deploy();

  await anchor.waitForDeployment();

  const address = await anchor.getAddress();
  console.log(`Badge83Anchor deploye: ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});