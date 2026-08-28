export function createMemoryStorage() {
  const values = new Map();
  return {
    async get(key) {
      return values.get(key);
    },
    async put(key, value) {
      values.set(key, structuredClone(value));
    },
    async delete(key) {
      return values.delete(key);
    },
    dump() {
      return new Map(values);
    }
  };
}
