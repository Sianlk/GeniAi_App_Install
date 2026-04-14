import crypto from 'node:crypto';

const WINDOW_MS = 90_000; // ±90 seconds replay protection window

/**
 * Generate an HMAC-SHA256 approval signature.
 * Payload: `actorEmail:suggestionId:timestamp`
 */
export function generateApprovalSignature(
  actorEmail: string,
  suggestionId: string,
  secret: string
): { signature: string; timestamp: number } {
  const timestamp = Date.now();
  const payload = `${actorEmail}:${suggestionId}:${timestamp}`;
  const signature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return { signature, timestamp };
}

/**
 * Verify an HMAC-SHA256 approval signature.
 * Returns true only if signature matches and timestamp is within ±90s.
 */
export function verifyApprovalSignature(
  actorEmail: string,
  suggestionId: string,
  timestamp: number,
  signature: string,
  secret: string
): boolean {
  const now = Date.now();
  if (Math.abs(now - timestamp) > WINDOW_MS) {
    return false; // replay or stale request
  }

  const payload = `${actorEmail}:${suggestionId}:${timestamp}`;
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  // Constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(expected, 'hex'),
    Buffer.from(signature, 'hex')
  );
}
