const RULES = {
  faculty: {
    notes: { type: "string", max: 20_000 },
    status: {
      type: "string",
      choices: ["discovered", "shortlisted", "contacted"]
    },
    match_analysis: { type: "object", max: 50_000 }
  },
  artifacts: {
    subject: { type: "string", max: 1_000 },
    content: { type: "string", max: 50_000 },
    status: { type: "string", choices: ["draft", "reviewed"] },
    review_note: { type: "string", max: 10_000 },
    planned_send_date: { type: "string", max: 32 },
    follow_up_date: { type: "string", max: 32 },
    requires_human_review: { type: "boolean" }
  }
};

const encoder = new TextEncoder();

function serializedSize(value) {
  return encoder.encode(typeof value === "string" ? value : JSON.stringify(value)).byteLength;
}

function matchesType(value, type) {
  if (type === "object") {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }
  return typeof value === type;
}

export function validatePatch(collection, patch) {
  const collectionRules = RULES[collection];
  if (!collectionRules) throw new Error("collection not editable");
  if (!patch || Array.isArray(patch) || typeof patch !== "object") {
    throw new Error("expected patch object");
  }

  const clean = {};
  for (const [field, value] of Object.entries(patch)) {
    const rule = collectionRules[field];
    if (!rule) throw new Error("field not editable");
    if (!matchesType(value, rule.type)) throw new Error("invalid field type");
    if (rule.choices && !rule.choices.includes(value)) throw new Error("invalid field value");
    if (rule.max && serializedSize(value) > rule.max) throw new Error("field too large");
    clean[field] = structuredClone(value);
  }

  if (Object.keys(clean).length === 0) throw new Error("empty patch");
  return clean;
}
