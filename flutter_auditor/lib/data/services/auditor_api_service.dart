import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/audit_report_model.dart';

class AuditorApiService {
  static const String localApiBase = 'http://localhost:8000';
  static const String cloudApiBase = 'https://a3-ps027-tc190.onrender.com';

  final http.Client _client;

  AuditorApiService({http.Client? client}) : _client = client ?? http.Client();

  Future<AuditReportDto> fetchAudit(String targetUrl) async {
    final uri = Uri.parse('$localApiBase/api/audit?url=${Uri.encodeComponent(targetUrl)}');
    try {
      final response = await _client.get(uri).timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return AuditReportDto.fromJson(data);
      }
    } catch (_) {
      // Fallback to cloud API
    }

    final cloudUri = Uri.parse('$cloudApiBase/api/audit?url=${Uri.encodeComponent(targetUrl)}');
    final response = await _client.get(cloudUri).timeout(const Duration(seconds: 30));
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return AuditReportDto.fromJson(data);
    } else {
      throw Exception('Audit failed with status: ${response.statusCode}');
    }
  }
}
