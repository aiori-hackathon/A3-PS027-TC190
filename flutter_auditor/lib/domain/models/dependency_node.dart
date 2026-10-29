enum ProtocolStatus {
  ipv6Ready,
  ipv4Only,
  brokenRoute,
  ipv4Literal,
}

/// Pure domain model for a node in the dependency graph mesh.
class DependencyNode {
  final String id;
  final String host;
  final String? remoteIp;
  final bool isApex;
  final bool isThirdParty;
  final ProtocolStatus status;
  final double? rttMs;
  final bool isIpv4Literal;
  final String? firstAaaa;
  final String? nameserverStatus;

  const DependencyNode({
    required this.id,
    required this.host,
    this.remoteIp,
    required this.isApex,
    required this.isThirdParty,
    required this.status,
    this.rttMs,
    this.isIpv4Literal = false,
    this.firstAaaa,
    this.nameserverStatus,
  });

  /// Actionable CLI verification command for this node.
  String get actionableCliCommand {
    if (isIpv4Literal) {
      return 'curl -6 --connect-timeout 4 -I -v http://$host';
    }
    if (status == ProtocolStatus.ipv4Only || firstAaaa == null) {
      return 'dig AAAA $host +dnssec +trace';
    }
    if (status == ProtocolStatus.brokenRoute) {
      return 'curl -6 --connect-timeout 4 -I -v https://$host';
    }
    return 'curl -6 -s -o /dev/null -w "HTTP: %{http_code} | TTFB: %{time_starttransfer}s\\n" https://$host';
  }
}
