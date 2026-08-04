function eventNumber(entry) {
  const match = String(entry?.event_id ?? "").match(/(\d+)$/);
  return match ? Number(match[1]) : -1;
}

export function latestEventEntry(entries) {
  return [...(entries || [])].sort((left, right) => {
    const numberDifference = eventNumber(right) - eventNumber(left);
    if (numberDifference) return numberDifference;
    return String(right?.event_id ?? "").localeCompare(String(left?.event_id ?? ""));
  })[0];
}
