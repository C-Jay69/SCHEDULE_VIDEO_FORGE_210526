import { PrismaClient } from '@prisma/client'
import { mkdirSync } from 'fs'
import { join } from 'path'

// Ensure the db directory exists
mkdirSync(join(process.cwd(), 'db'), { recursive: true })

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const db =
  globalForPrisma.prisma ??
  new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = db
