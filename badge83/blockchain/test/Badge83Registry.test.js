const { expect } = require("chai");
const { ethers } = require("hardhat");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");

describe("Badge83Registry", function () {
  async function deployRegistry() {
    const [owner, operator, unauthorized, newOwner] = await ethers.getSigners();
    const Badge83Registry = await ethers.getContractFactory("Badge83Registry");
    const registry = await Badge83Registry.deploy();
    await registry.waitForDeployment();
    return { registry, owner, operator, unauthorized, newOwner };
  }

  const credentialHash = "0x" + "a".repeat(64);
  const otherCredentialHash = "0x" + "b".repeat(64);

  it("definit le deployer comme owner", async function () {
    const { registry, owner } = await deployRegistry();

    expect(await registry.owner()).to.equal(owner.address);
  });

  it("emet OwnershipTransferred au deploiement", async function () {
    const [owner] = await ethers.getSigners();
    const Badge83Registry = await ethers.getContractFactory("Badge83Registry");
    const registry = await Badge83Registry.deploy();

    await expect(registry.deploymentTransaction())
      .to.emit(registry, "OwnershipTransferred")
      .withArgs(ethers.ZeroAddress, owner.address);
  });

  it("permet au owner de transferer ownership", async function () {
    const { registry, owner, newOwner } = await deployRegistry();

    await expect(registry.transferOwnership(newOwner.address))
      .to.emit(registry, "OwnershipTransferred")
      .withArgs(owner.address, newOwner.address);

    expect(await registry.owner()).to.equal(newOwner.address);
  });

  it("refuse transferOwnership vers zero address", async function () {
    const { registry } = await deployRegistry();

    await expect(registry.transferOwnership(ethers.ZeroAddress)).to.be.revertedWith("INVALID_OWNER");
  });

  it("refuse transferOwnership par un compte non owner", async function () {
    const { registry, unauthorized, newOwner } = await deployRegistry();

    await expect(
      registry.connect(unauthorized).transferOwnership(newOwner.address)
    ).to.be.revertedWith("ONLY_OWNER");
  });

  it("permet au owner de configurer un operateur", async function () {
    const { registry, operator } = await deployRegistry();

    await expect(registry.setOperator(operator.address, true))
      .to.emit(registry, "OperatorUpdated")
      .withArgs(operator.address, true);

    expect(await registry.operators(operator.address)).to.equal(true);
  });

  it("refuse de configurer zero address comme operateur", async function () {
    const { registry } = await deployRegistry();

    await expect(registry.setOperator(ethers.ZeroAddress, true)).to.be.revertedWith("INVALID_OPERATOR");
  });

  it("refuse setOperator par un compte non owner", async function () {
    const { registry, unauthorized, operator } = await deployRegistry();

    await expect(
      registry.connect(unauthorized).setOperator(operator.address, true)
    ).to.be.revertedWith("ONLY_OWNER");
  });

  it("permet au owner d'ancrer un hash bytes32 valide", async function () {
    const { registry, owner } = await deployRegistry();

    await expect(registry.anchor(credentialHash))
      .to.emit(registry, "CredentialAnchored")
      .withArgs(credentialHash, owner.address, anyValue);

    const [anchored, revoked, anchoredAt, revokedAt, anchoredBy, revokedBy] =
      await registry.getStatus(credentialHash);

    expect(anchored).to.equal(true);
    expect(revoked).to.equal(false);
    expect(anchoredAt).to.be.greaterThan(0);
    expect(revokedAt).to.equal(0);
    expect(anchoredBy).to.equal(owner.address);
    expect(revokedBy).to.equal(ethers.ZeroAddress);
    expect(await registry.isValid(credentialHash)).to.equal(true);
  });

  it("permet a un operateur autorise d'ancrer et revoquer", async function () {
    const { registry, operator } = await deployRegistry();
    await registry.setOperator(operator.address, true);

    await registry.connect(operator).anchor(credentialHash);
    await expect(registry.connect(operator).revoke(credentialHash))
      .to.emit(registry, "CredentialRevoked")
      .withArgs(credentialHash, operator.address, anyValue);

    const [anchored, revoked, , revokedAt, anchoredBy, revokedBy] =
      await registry.getStatus(credentialHash);

    expect(anchored).to.equal(true);
    expect(revoked).to.equal(true);
    expect(revokedAt).to.be.greaterThan(0);
    expect(anchoredBy).to.equal(operator.address);
    expect(revokedBy).to.equal(operator.address);
    expect(await registry.isValid(credentialHash)).to.equal(false);
  });

  it("refuse anchor et revoke par un compte non autorise", async function () {
    const { registry, unauthorized } = await deployRegistry();

    await expect(registry.connect(unauthorized).anchor(credentialHash)).to.be.revertedWith("NOT_AUTHORIZED");
    await expect(registry.connect(unauthorized).revoke(credentialHash)).to.be.revertedWith("NOT_AUTHORIZED");
  });

  it("refuse le hash nul a l'ancrage et a la revocation", async function () {
    const { registry } = await deployRegistry();

    await expect(registry.anchor(ethers.ZeroHash)).to.be.revertedWith("INVALID_HASH");
    await expect(registry.revoke(ethers.ZeroHash)).to.be.revertedWith("INVALID_HASH");
  });

  it("refuse un double ancrage du meme hash", async function () {
    const { registry } = await deployRegistry();

    await registry.anchor(credentialHash);

    await expect(registry.anchor(credentialHash)).to.be.revertedWith("ALREADY_ANCHORED");
  });

  it("refuse la revocation d'un hash non ancre", async function () {
    const { registry } = await deployRegistry();

    await expect(registry.revoke(credentialHash)).to.be.revertedWith("NOT_ANCHORED");
  });

  it("refuse une double revocation", async function () {
    const { registry } = await deployRegistry();

    await registry.anchor(credentialHash);
    await registry.revoke(credentialHash);

    await expect(registry.revoke(credentialHash)).to.be.revertedWith("ALREADY_REVOKED");
  });

  it("getStatus retourne false false pour un hash inconnu", async function () {
    const { registry } = await deployRegistry();

    const [anchored, revoked, anchoredAt, revokedAt, anchoredBy, revokedBy] =
      await registry.getStatus(otherCredentialHash);

    expect(anchored).to.equal(false);
    expect(revoked).to.equal(false);
    expect(anchoredAt).to.equal(0);
    expect(revokedAt).to.equal(0);
    expect(anchoredBy).to.equal(ethers.ZeroAddress);
    expect(revokedBy).to.equal(ethers.ZeroAddress);
    expect(await registry.isValid(otherCredentialHash)).to.equal(false);
  });

  it("permet de retirer un operateur", async function () {
    const { registry, operator } = await deployRegistry();

    await registry.setOperator(operator.address, true);
    await registry.setOperator(operator.address, false);

    expect(await registry.operators(operator.address)).to.equal(false);
    await expect(registry.connect(operator).anchor(credentialHash)).to.be.revertedWith("NOT_AUTHORIZED");
  });

  it("ne stocke aucune donnee personnelle", async function () {
    const { registry } = await deployRegistry();

    await registry.anchor(credentialHash);
    await registry.revoke(credentialHash);

    expect(registry.adminRecipient).to.equal(undefined);
    expect(registry.assertionId).to.equal(undefined);
    expect(registry.email).to.equal(undefined);
    expect(registry.name).to.equal(undefined);
    expect(registry.revocationReason).to.equal(undefined);
    expect(registry.assertionJson).to.equal(undefined);
    expect(registry.canonicalPayload).to.equal(undefined);
  });
});