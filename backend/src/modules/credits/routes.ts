import { FastifyInstance } from 'fastify';
import Stripe from 'stripe';
import { z } from 'zod';
import { env } from '../../config.js';
import { prisma } from '../../db.js';

const stripe = new Stripe(env.STRIPE_SECRET_KEY);

const BuyInput = z.object({
  credits: z.number().int().min(100),
  accountId: z.string().optional(),
});

const SpendInput = z.object({
  amountPence: z.number().int().positive(),
  reason: z.string().min(2),
  appSlug: z.string().min(2),
});

export async function creditRoutes(app: FastifyInstance) {
  app.get('/api/credits/balance', { preHandler: [app.authenticate] }, async (req) => {
    const user = req.user as { userId: string };
    const row = await prisma.user.findUniqueOrThrow({ where: { id: user.userId } });
    return {
      creditsPence: row.creditsPence.toString(),
      currency: 'GBP',
    };
  });

  app.post('/api/credits/buy', { preHandler: [app.authenticate] }, async (req) => {
    const user = req.user as { userId: string; email: string };
    const input = BuyInput.parse(req.body);

    const amountPence = input.credits;
    const session = await stripe.checkout.sessions.create({
      mode: 'payment',
      payment_method_types: ['card'],
      customer_email: user.email,
      line_items: [
        {
          quantity: 1,
          price_data: {
            currency: 'gbp',
            product_data: { name: `Platform Credits (${input.credits})` },
            unit_amount: amountPence,
          },
        },
      ],
      payment_intent_data: {
        transfer_data: input.accountId ? { destination: input.accountId } : undefined,
        metadata: {
          userId: user.userId,
          creditsPence: String(amountPence),
        },
      },
      success_url: 'https://hosturserver.com/success',
      cancel_url: 'https://hosturserver.com/cancel',
    });

    return { checkoutUrl: session.url };
  });

  app.post('/api/credits/spend', { preHandler: [app.authenticate] }, async (req) => {
    const user = req.user as { userId: string };
    const input = SpendInput.parse(req.body);

    return prisma.$transaction(async (tx) => {
      const current = await tx.user.findUniqueOrThrow({ where: { id: user.userId } });
      if (current.creditsPence < BigInt(input.amountPence)) {
        throw new Error('insufficient_credits');
      }

      const updated = await tx.user.update({
        where: { id: user.userId },
        data: { creditsPence: current.creditsPence - BigInt(input.amountPence) },
      });

      await tx.creditTxn.create({
        data: {
          userId: user.userId,
          type: 'SPEND',
          amountPence: BigInt(-input.amountPence),
          currency: 'GBP',
          meta: { reason: input.reason, appSlug: input.appSlug },
        },
      });

      return { creditsPence: updated.creditsPence.toString(), currency: 'GBP' };
    });
  });
}
