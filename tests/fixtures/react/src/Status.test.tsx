import { describe, expect, it } from 'vitest';
import { Status } from './Status';

describe('Status', () => {
  it('returns an accessible status element description', () => {
    expect(Status({ message: 'Ready' }).props.role).toBe('status');
  });
});
