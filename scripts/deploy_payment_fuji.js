/**
 * Deploy PaymentRegistry to Avalanche Fuji testnet.
 * 
 * Requirements:
 *   npm install ethers@6 solc
 *   
 * Environment variables:
 *   FUJI_PRIVATE_KEY  — deployer private key (with Fuji AVAX for gas)
 *   FUJI_RPC_URL      — (optional) defaults to public Fuji RPC
 *   REGISTRATION_FEE  — (optional) fee in wei, defaults to 0
 * 
 * Usage:
 *   node scripts/deploy_payment_fuji.js
 */

const { ethers } = require("ethers");
const solc = require("solc");
const fs = require("fs");
const path = require("path");

async function main() {
  const privateKey = process.env.FUJI_PRIVATE_KEY;
  if (!privateKey) {
    console.error("ERROR: FUJI_PRIVATE_KEY environment variable is required.");
    console.error("Set it to a private key that has Fuji testnet AVAX for gas.");
    console.error("Get test AVAX from https://faucet.avax.network/");
    console.error("");
    console.error("Example:");
    console.error("  set FUJI_PRIVATE_KEY=0xYOUR_PRIVATE_KEY");
    console.error("  node scripts/deploy_payment_fuji.js");
    process.exit(1);
  }

  const rpcUrl = process.env.FUJI_RPC_URL || "https://api.avax-test.network/ext/bc/C/rpc";
  const fee = process.env.REGISTRATION_FEE || "0";

  console.log("Compiling PaymentRegistry.sol...");
  const contractPath = path.join(__dirname, "..", "backend", "contracts", "PaymentRegistry.sol");
  const source = fs.readFileSync(contractPath, "utf8");

  const input = {
    language: "Solidity",
    sources: { "PaymentRegistry.sol": { content: source } },
    settings: { outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } } },
  };

  const output = JSON.parse(solc.compile(JSON.stringify(input)));

  if (output.errors) {
    const fatal = output.errors.filter(e => e.severity === "error");
    if (fatal.length > 0) {
      console.error("Compilation errors:");
      fatal.forEach(e => console.error(e.formattedMessage));
      process.exit(1);
    }
  }

  const contract = output.contracts["PaymentRegistry.sol"]["PaymentRegistry"];
  const abi = contract.abi;
  const bytecode = "0x" + contract.evm.bytecode.object;

  console.log(`Connecting to Fuji: ${rpcUrl}`);
  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const wallet = new ethers.Wallet(privateKey, provider);

  const balance = await provider.getBalance(wallet.address);
  console.log(`Deployer: ${wallet.address}`);
  console.log(`Balance: ${ethers.formatEther(balance)} AVAX`);

  if (balance === 0n) {
    console.error("ERROR: Deployer has 0 AVAX. Get test AVAX from https://faucet.avax.network/");
    process.exit(1);
  }

  console.log(`Deploying with fee=${fee} wei...`);
  const factory = new ethers.ContractFactory(abi, bytecode, wallet);
  const deployed = await factory.deploy(fee);
  await deployed.waitForDeployment();

  const address = await deployed.getAddress();
  console.log("");
  console.log("═══════════════════════════════════════");
  console.log("  PaymentRegistry deployed!");
  console.log(`  Address: ${address}`);
  console.log(`  TX Hash: ${deployed.deploymentTransaction()?.hash}`);
  console.log(`  Fee:     ${fee} wei`);
  console.log(`  Network: Avalanche Fuji (43113)`);
  console.log("═══════════════════════════════════════");
  console.log("");
  console.log("Add to frontend .env:");
  console.log(`  VITE_PAYMENT_CONTRACT=${address}`);

  // Save ABI for frontend
  const abiPath = path.join(__dirname, "..", "frontend", "src", "lib", "PaymentRegistryABI.json");
  fs.writeFileSync(abiPath, JSON.stringify(abi, null, 2));
  console.log(`ABI saved to: ${abiPath}`);
}

main().catch(console.error);
