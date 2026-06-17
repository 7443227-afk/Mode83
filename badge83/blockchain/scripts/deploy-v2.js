const hre = require("hardhat");

async function main() {
  const Badge83AnchorV2 = await hre.ethers.getContractFactory("Badge83AnchorV2");
  const anchor = await Badge83AnchorV2.deploy();

  await anchor.waitForDeployment();

  const address = await anchor.getAddress();
  console.log(`Badge83AnchorV2 deploye: ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});