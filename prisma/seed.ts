import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcryptjs'

const prisma = new PrismaClient()

async function main() {
  const adminEmail = 'admin@videoforge.dev'
  const adminPassword = 'admin123'

  const existing = await prisma.user.findUnique({ where: { email: adminEmail } })
  if (existing) {
    console.log('Admin user already exists, skipping seed.')
    return
  }

  const hashedPassword = await bcrypt.hash(adminPassword, 10)
  await prisma.user.create({
    data: {
      id: 'admin_001',
      email: adminEmail,
      password: hashedPassword,
      name: 'Admin',
      isAdmin: true,
      plan: 'pro',
    },
  })
  console.log('Admin user created successfully.')
  console.log(`  Email: ${adminEmail}`)
  console.log(`  Password: ${adminPassword}`)
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
