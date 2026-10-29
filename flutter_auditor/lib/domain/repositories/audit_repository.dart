import '../models/audit_score.dart';
import '../models/dependency_node.dart';

class AuditResult {
  final String targetUrl;
  final AuditScore score;
  final List<DependencyNode> nodes;
  final DateTime auditedAt;

  const AuditResult({
    required this.targetUrl,
    required this.score,
    required this.nodes,
    required this.auditedAt,
  });
}

/// Abstract contract for audit data fetching (Domain Layer).
abstract class AuditRepository {
  Future<AuditResult> runAudit(String targetUrl);
}
