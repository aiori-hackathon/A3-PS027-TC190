/// Pure domain entity representing IPv6 readiness score and metrics.
class AuditScore {
  final double scorePercent;
  final String verdict;
  final String letterGrade;
  final int totalSubresources;
  final int ipv6Subresources;
  final int ipv4Subresources;
  final bool apexHasAaaa;
  final double? ipv6TtfbMs;
  final double? ipv4TtfbMs;

  const AuditScore({
    required this.scorePercent,
    required this.verdict,
    required this.letterGrade,
    required this.totalSubresources,
    required this.ipv6Subresources,
    required this.ipv4Subresources,
    required this.apexHasAaaa,
    this.ipv6TtfbMs,
    this.ipv4TtfbMs,
  });

  /// True if the apex domain and subresources are completely ready.
  bool get isPureIpv6Ready => apexHasAaaa && scorePercent >= 95.0;

  /// Subresource ratio as a formatted string (e.g. "142 / 168").
  String get subresourceRatioString => '$ipv6Subresources / $totalSubresources';

  /// Subresource dual-stack percentage.
  double get subresourcePercentage =>
      totalSubresources > 0 ? (ipv6Subresources / totalSubresources) * 100.0 : 0.0;

  /// Latency differential (v6 - v4) in milliseconds.
  double? get latencyDeltaMs {
    if (ipv6TtfbMs != null && ipv4TtfbMs != null) {
      return ipv6TtfbMs! - ipv4TtfbMs!;
    }
    return null;
  }
}
