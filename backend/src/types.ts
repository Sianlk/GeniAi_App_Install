import { FastifyRequest } from 'fastify';

export type JwtUser = {
  userId: string;
  email: string;
  role: 'USER' | 'ADMIN' | 'SUPER_ADMIN';
  tokenVersion: number;
};

export type AuthedRequest = FastifyRequest & {
  user: JwtUser;
};
