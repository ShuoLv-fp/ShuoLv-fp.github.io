function positiveRank(record) {
  const rank = Number(record?.featured_rank);
  return Number.isFinite(rank) && rank > 0 ? rank : null;
}

function fitScore(record) {
  const score = Number(record?.fit?.total);
  return Number.isFinite(score) ? score : -1;
}

function text(value) {
  return String(value || "").trim();
}

export function orderFaculty(records) {
  if (!Array.isArray(records)) return [];
  return [...records].sort((left, right) => {
    const leftRank = positiveRank(left);
    const rightRank = positiveRank(right);
    if (leftRank !== null || rightRank !== null) {
      if (leftRank === null) return 1;
      if (rightRank === null) return -1;
      if (leftRank !== rightRank) return leftRank - rightRank;
    }

    const scoreDifference = fitScore(right) - fitScore(left);
    if (scoreDifference) return scoreDifference;
    const nameDifference = text(left?.display_name || left?.name)
      .localeCompare(text(right?.display_name || right?.name), "en", { sensitivity: "base" });
    if (nameDifference) return nameDifference;
    return text(left?.institution)
      .localeCompare(text(right?.institution), "en", { sensitivity: "base" });
  });
}
