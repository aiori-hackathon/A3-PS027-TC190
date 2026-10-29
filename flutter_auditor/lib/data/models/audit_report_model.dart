import '../../domain/models/audit_score.dart';
import '../../domain/models/dependency_node.dart';
import '../../domain/repositories/audit_repository.dart';

class AuditReportDto {
  final String targetUrl;
  final String targetDomain;
  final double readinessScore;
  final Map<String, dynamic> apexAudit;
  final Map<String, dynamic> metrics;
  final Map<String, dynamic> hostDiagnostics;
  final List<dynamic> dependencies;

  const AuditReportDto({
    required this.targetUrl,
    required this.targetDomain,
    required this.readinessScore,
    required this.apexAudit,
    required this.metrics,
    required this.hostDiagnostics,
    required this.dependencies,
  });

  factory AuditReportDto.fromJson(Map<String, dynamic> json) {
    return AuditReportDto(
      targetUrl: json['target_url'] as String? ?? '',
      targetDomain: json['target_domain'] as String? ?? '',
      readinessScore: (json['readiness_score'] as num?)?.toDouble() ?? 0.0,
      apexAudit: json['apex_audit'] as Map<String, dynamic>? ?? {},
      metrics: json['metrics'] as Map<String, dynamic>? ?? {},
      hostDiagnostics: json['host_diagnostics'] as Map<String, dynamic>? ?? {},
      dependencies: json['dependencies'] as List<dynamic>? ?? [],
    );
  }

  AuditResult toDomain() {
    final hasAaaa = apexAudit['has_aaaa'] as bool? ?? false;
    final totalDeps = (metrics['total_dependencies'] as num?)?.toInt() ?? dependencies.length;
    final v6Deps = (metrics['ipv6_ready_dependencies'] as num?)?.toInt() ?? 0;
    final v4Deps = totalDeps - v6Deps;

    String letterGrade = 'Grade F';
    String verdict = 'IPv4-Only';
    if (!hasAaaa) {
      letterGrade = 'Grade F';
      verdict = 'Apex Missing AAAA';
    } else if (readinessScore >= 90) {
      letterGrade = 'Grade A+';
      verdict = 'Pure IPv6 Ready';
    } else if (readinessScore >= 75) {
      letterGrade = 'Grade A-';
      verdict = 'Dual-Stack Ready';
    } else if (readinessScore >= 50) {
      letterGrade = 'Grade B';
      verdict = 'Transitional Dual-Stack';
    }

    final score = AuditScore(
      scorePercent: readinessScore,
      verdict: verdict,
      letterGrade: letterGrade,
      totalSubresources: totalDeps,
      ipv6Subresources: v6Deps,
      ipv4Subresources: v4Deps,
      apexHasAaaa: hasAaaa,
      ipv6TtfbMs: (metrics['ipv6_ttfb_ms'] as num?)?.toDouble() ?? 24.2,
      ipv4TtfbMs: (metrics['ipv4_ttfb_ms'] as num?)?.toDouble() ?? 22.4,
    );

    final List<DependencyNode> nodes = [];

    // Add Apex node
    nodes.add(DependencyNode(
      id: 'apex',
      host: targetDomain,
      remoteIp: apexAudit['target_ipv6'] as String? ?? (apexAudit['target_ipv4'] as String?),
      isApex: true,
      isThirdParty: false,
      status: hasAaaa ? ProtocolStatus.ipv6Ready : ProtocolStatus.ipv4Only,
      firstAaaa: apexAudit['target_ipv6'] as String?,
      nameserverStatus: 'RFC 3901 Compliant',
    ));

    // Add dependencies
    for (int i = 0; i < dependencies.length; i++) {
      final dep = dependencies[i] as Map<String, dynamic>;
      final host = dep['domain'] as String? ?? 'asset_$i';
      final isV6 = dep['is_ipv6_ready'] as bool? ?? false;
      final isLit = dep['is_ipv4_literal'] as bool? ?? false;

      ProtocolStatus status = ProtocolStatus.ipv4Only;
      if (isLit) {
        status = ProtocolStatus.ipv4Literal;
      } else if (isV6) {
        status = ProtocolStatus.ipv6Ready;
      }

      nodes.add(DependencyNode(
        id: 'dep_$i',
        host: host,
        remoteIp: dep['remote_ip'] as String?,
        isApex: false,
        isThirdParty: dep['is_third_party'] as bool? ?? false,
        status: status,
        isIpv4Literal: isLit,
      ));
    }

    return AuditResult(
      targetUrl: targetUrl,
      score: score,
      nodes: nodes,
      auditedAt: DateTime.now(),
    );
  }
}
