import 'package:flutter/foundation.dart';
import '../../../../domain/models/dependency_node.dart';
import '../../../../domain/repositories/audit_repository.dart';

class VisualizerViewModel extends ChangeNotifier {
  final AuditRepository _repository;

  VisualizerViewModel({required AuditRepository repository})
      : _repository = repository;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  AuditResult? _auditResult;
  AuditResult? get auditResult => _auditResult;

  DependencyNode? _selectedNode;
  DependencyNode? get selectedNode => _selectedNode;

  String _targetUrl = 'https://api.github.com';
  String get targetUrl => _targetUrl;

  Future<void> audit(String url) async {
    _targetUrl = url;
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final result = await _repository.runAudit(url);
      _auditResult = result;
      if (result.nodes.isNotEmpty) {
        _selectedNode = result.nodes.first;
      }
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void selectNode(DependencyNode node) {
    _selectedNode = node;
    notifyListeners();
  }
}
