const { expect } = require("chai");
const { ethers } = require("hardhat");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");

describe("Badge83Anchor", function () {
  async function deployerContrat() {
    const [operateur, autreCompte] = await ethers.getSigners();
    const Badge83Anchor = await ethers.getContractFactory("Badge83Anchor");
    const anchor = await Badge83Anchor.deploy();
    await anchor.waitForDeployment();
    return { anchor, operateur, autreCompte };
  }

  const hashCredential = "0x" + "a".repeat(64);
  const autreHashCredential = "0x" + "b".repeat(64);

  it("ancre un hash bytes32 valide", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);

    expect(await anchor.anchored(hashCredential)).to.equal(true);
  });

  it("emet un evenement sans donnee personnelle", async function () {
    const { anchor, operateur } = await deployerContrat();

    await expect(anchor.anchor(hashCredential))
      .to.emit(anchor, "CredentialHashAnchored")
      .withArgs(hashCredential, operateur.address, anyValue);
  });

  it("refuse un double ancrage du meme hash", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);

    await expect(anchor.anchor(hashCredential)).to.be.revertedWith("Hash deja ancre");
  });

  it("refuse le hash nul", async function () {
    const { anchor } = await deployerContrat();

    await expect(anchor.anchor(ethers.ZeroHash)).to.be.revertedWith("Hash invalide");
  });

  it("permet a plusieurs comptes d'ancrer des hashes differents", async function () {
    const { anchor, autreCompte } = await deployerContrat();

    await anchor.anchor(hashCredential);
    await anchor.connect(autreCompte).anchor(autreHashCredential);

    expect(await anchor.anchored(hashCredential)).to.equal(true);
    expect(await anchor.anchored(autreHashCredential)).to.equal(true);
  });

  it("ne stocke que l'etat booleen associe au hash", async function () {
    const { anchor } = await deployerContrat();

    await anchor.anchor(hashCredential);

    const stockagePublic = await anchor.anchored(hashCredential);

    expect(stockagePublic).to.equal(true);
    expect(anchor.adminRecipient).to.equal(undefined);
    expect(anchor.assertionJson).to.equal(undefined);
    expect(anchor.canonicalPayload).to.equal(undefined);
  });
});
