import '../../domain/repositories/audit_repository.dart';
import '../services/auditor_api_service.dart';

class AuditRepositoryImpl implements AuditRepository {
  final AuditorApiService _apiService;

  AuditRepositoryImpl({AuditorApiService? apiService})
      : _apiService = apiService ?? AuditorApiService();

  @override
  Future<AuditResult> runAudit(String targetUrl) async {
    final dto = await _apiService.fetchAudit(targetUrl);
    return dto.toDomain();
  }
}
