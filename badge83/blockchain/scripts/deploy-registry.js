const hre = require("hardhat");

async function main() {
  const Badge83Registry = await hre.ethers.getContractFactory("Badge83Registry");
  const registry = await Badge83Registry.deploy();

  await registry.waitForDeployment();

  const address = await registry.getAddress();
  const network = await hre.ethers.provider.getNetwork();

  console.log(`Badge83Registry deployed: ${address}`);
  console.log(`network: ${hre.network.name}`);
  console.log(`chainId: ${network.chainId.toString()}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});