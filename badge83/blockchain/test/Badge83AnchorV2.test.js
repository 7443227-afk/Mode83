const { expect } = require("chai");
const { ethers } = require("hardhat");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");

describe("Badge83AnchorV2", function () {
  async function deployerContrat() {
    const [operateur, autreCompte] = await ethers.getSigners();
    const Badge83AnchorV2 = await ethers.getContractFactory("Badge83AnchorV2");
    const anchor = await Badge83AnchorV2.deploy();
    await anchor.waitForDeployment();
    return { anchor, operateur, autreCompte };
  }

  const hashCredential = "0x" + "a".repeat(64);
  const autreHashCredential = "0x" + "b".repeat(64);

  it("ancre un hash bytes32 valide", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);

    expect(await anchor.anchored(hashCredential)).to.equal(true);
    expect(await anchor.isAnchored(hashCredential)).to.equal(true);
    expect(await anchor.revoked(hashCredential)).to.equal(false);
  });

  it("emet un evenement d'ancrage sans donnee personnelle", async function () {
    const { anchor, operateur } = await deployerContrat();

    await expect(anchor.anchor(hashCredential))
      .to.emit(anchor, "CredentialHashAnchored")
      .withArgs(hashCredential, operateur.address, anyValue);
  });

  it("refuse le hash nul a l'ancrage", async function () {
    const { anchor } = await deployerContrat();

    await expect(anchor.anchor(ethers.ZeroHash)).to.be.revertedWith("Hash invalide");
  });

  it("refuse un double ancrage du meme hash", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);

    await expect(anchor.anchor(hashCredential)).to.be.revertedWith("Hash deja ancre");
  });

  it("revoque un hash ancre", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);
    await anchor.revoke(hashCredential);

    expect(await anchor.revoked(hashCredential)).to.equal(true);
    expect(await anchor.isRevoked(hashCredential)).to.equal(true);
  });

  it("emet un evenement de revocation sans donnee personnelle", async function () {
    const { anchor, operateur } = await deployerContrat();

    await anchor.anchor(hashCredential);

    await expect(anchor.revoke(hashCredential))
      .to.emit(anchor, "CredentialHashRevoked")
      .withArgs(hashCredential, operateur.address, anyValue);
  });

  it("refuse le hash nul a la revocation", async function () {
    const { anchor } = await deployerContrat();

    await expect(anchor.revoke(ethers.ZeroHash)).to.be.revertedWith("Hash invalide");
  });

  it("refuse la revocation d'un hash non ancre", async function () {
    const { anchor } = await deployerContrat();

    await expect(anchor.revoke(hashCredential)).to.be.revertedWith("Hash non ancre");
  });

  it("refuse une double revocation", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);
    await anchor.revoke(hashCredential);

    await expect(anchor.revoke(hashCredential)).to.be.revertedWith("Hash deja revoque");
  });

  it("getStatus retourne true false apres ancrage", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);

    const [isHashAnchored, isHashRevoked] = await anchor.getStatus(hashCredential);

    expect(isHashAnchored).to.equal(true);
    expect(isHashRevoked).to.equal(false);
  });

  it("getStatus retourne true true apres revocation", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);
    await anchor.revoke(hashCredential);
    const [isHashAnchored, isHashRevoked] = await anchor.getStatus(hashCredential);

    expect(isHashAnchored).to.equal(true);
    expect(isHashRevoked).to.equal(true);
  });

  it("permet a plusieurs comptes d'ancrer et revoquer des hashes connus", async function () {
    const { anchor, autreCompte } = await deployerContrat();

    await anchor.anchor(hashCredential);
    await anchor.connect(autreCompte).anchor(autreHashCredential);
    await anchor.connect(autreCompte).revoke(hashCredential);

    expect(await anchor.anchored(autreHashCredential)).to.equal(true);
    expect(await anchor.revoked(hashCredential)).to.equal(true);
  });

  it("ne stocke toujours aucune donnee personnelle", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);
    await anchor.revoke(hashCredential);

    expect(await anchor.anchored(hashCredential)).to.equal(true);
    expect(await anchor.revoked(hashCredential)).to.equal(true);
    expect(anchor.adminRecipient).to.equal(undefined);
    expect(anchor.assertionId).to.equal(undefined);
    expect(anchor.revocationReason).to.equal(undefined);
    expect(anchor.assertionJson).to.equal(undefined);
    expect(anchor.canonicalPayload).to.equal(undefined);
  });
});