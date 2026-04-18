import { Queue } from 'bullmq';
import { redis } from '../redis.js';

export const workforceQueue = new Queue('workforce-tasks', {
  connection: redis,
});
