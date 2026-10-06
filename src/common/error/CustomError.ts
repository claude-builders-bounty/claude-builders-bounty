export interface CustomErrorAttributes {
  name: string;
  message: string;
  metadata?: Record<string, unknown>;
  stack?: string;
}

export class CustomError extends Error {
  public readonly name: string;
  public readonly metadata?: Record<string, unknown>;

  constructor(attributes: CustomErrorAttributes | string) {
    const attrs =
      typeof attributes === 'string'
        ? { name: 'ERROR', message: attributes }
        : attributes;

    super(attrs.message);
    this.name = attrs.name;
    this.metadata = attrs.metadata;
    Error.captureStackTrace(this, this.constructor);
  }

  toJSON(): Record<string, unknown> {
    const { name, message, metadata, stack } = this;
    return { name, message, metadata, stack };
  }
}
