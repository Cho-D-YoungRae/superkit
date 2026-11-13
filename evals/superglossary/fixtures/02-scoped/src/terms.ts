// Tokens grant access rights.
export function issueToken(): string { return "token"; }
// Bonds are financial securities issued to investors.
export function issueBond(): string { return "bond"; }
// External contract retains this token timestamp field.
export type TokenResponse = { issuedAt: string };
// Context absent: could be bond issuance or token granting.
export function issue(value: unknown): unknown { return value; }
