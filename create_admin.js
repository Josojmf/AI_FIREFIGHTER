// create_bo_admin.js
const { MongoClient } = require("mongodb");
const bcrypt = require("bcryptjs");

const uri = "mongodb+srv://joso:XyGItdDKpWkfJfjT@cluster0.yzzh9ig.mongodb.net/FIREFIGHTER";

async function run() {
  const client = new MongoClient(uri);
  try {
    await client.connect();
    const db = client.db("FIREFIGHTER");

    const username = "boadmin";
    const passwordPlain = "BoAdmin2024!";
    const hash = await bcrypt.hash(passwordPlain, 10);

    const userDoc = {
      username: username,
      email: "boadmin@firefighter.com",
      role: "admin",
      status: "active",
      mfa_enabled: false,
      created_at: new Date(),
      password_hash: hash
    };

    console.log("=== Insertando en users ===");
    await db.collection("users").updateOne(
      { username: username },
      { $set: userDoc },
      { upsert: true }
    );

    console.log("=== Insertando en Adm_Users ===");
    await db.collection("Adm_Users").updateOne(
      { username: username },
      { $set: userDoc },
      { upsert: true }
    );

    console.log("✅ Usuario 'boadmin' creado/actualizado en users y Adm_Users");
  } catch (err) {
    console.error("Error:", err);
  } finally {
    await client.close();
  }
}

run();
