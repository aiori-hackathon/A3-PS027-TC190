import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../../domain/models/dependency_node.dart';
import '../../../core/theme/primer_theme.dart';
import '../../../core/widgets/metric_card.dart';
import '../../../core/widgets/protocol_badge.dart';
import '../view_models/visualizer_view_model.dart';
import 'topology_mesh_painter.dart';

const double largeScreenBreakpoint = 800.0;

class VisualizerScreen extends StatefulWidget {
  final VisualizerViewModel viewModel;

  const VisualizerScreen({super.key, required this.viewModel});

  @override
  State<VisualizerScreen> createState() => _VisualizerScreenState();
}

class _VisualizerScreenState extends State<VisualizerScreen> {
  final TextEditingController _urlController = TextEditingController(text: 'https://api.github.com');

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: PrimerTheme.bgPage,
      appBar: AppBar(
        backgroundColor: PrimerTheme.bgPage,
        elevation: 0,
        title: Row(
          children: [
            const Icon(Icons.language, color: PrimerTheme.stateInfo, size: 20),
            const SizedBox(width: 8),
            const Text(
              'IPv6 Readiness Auditor',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: PrimerTheme.surfaceCard,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: PrimerTheme.borderDefault),
              ),
              child: const Text(
                'v2.4 Engine',
                style: TextStyle(fontSize: 10, color: PrimerTheme.textMuted, fontFamily: 'monospace'),
              ),
            ),
          ],
        ),
      ),
      body: ListenableBuilder(
        listenable: widget.viewModel,
        builder: (context, _) {
          return LayoutBuilder(
            builder: (context, constraints) {
              final isLargeScreen = constraints.maxWidth > largeScreenBreakpoint;

              return SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1200),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _buildSearchRow(),
                        const SizedBox(height: 16),
                        if (widget.viewModel.isLoading)
                          const Center(
                            child: Padding(
                              padding: EdgeInsets.all(32),
                              child: CircularProgressIndicator(),
                            ),
                          )
                        else if (widget.viewModel.auditResult != null) ...[
                          _buildScoreAndMetricsGrid(isLargeScreen),
                          const SizedBox(height: 16),
                          if (isLargeScreen)
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Expanded(flex: 7, child: _buildTopologyCard()),
                                const SizedBox(width: 16),
                                Expanded(flex: 5, child: _buildInspectorDrawer()),
                              ],
                            )
                          else ...[
                            _buildTopologyCard(),
                            const SizedBox(height: 16),
                            _buildInspectorDrawer(),
                          ],
                        ] else
                          _buildEmptyState(),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildSearchRow() {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: PrimerTheme.surfaceCard,
        borderRadius: BorderRadius.circular(PrimerTheme.radiusDefault),
        border: Border.all(color: PrimerTheme.borderDefault),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _urlController,
              style: const TextStyle(fontSize: 13, fontFamily: 'monospace', color: PrimerTheme.textPrimary),
              decoration: const InputDecoration(
                hintText: 'Enter target domain or URL (e.g. https://api.github.com)',
                hintStyle: TextStyle(color: PrimerTheme.textDim, fontSize: 13),
                prefixIcon: Icon(Icons.search, size: 18, color: PrimerTheme.textDim),
                border: InputBorder.none,
                isDense: true,
              ),
            ),
          ),
          ElevatedButton.icon(
            onPressed: () => widget.viewModel.audit(_urlController.text.trim()),
            icon: const Icon(Icons.play_arrow, size: 16),
            label: const Text('Audit Endpoint'),
            style: ElevatedButton.styleFrom(
              backgroundColor: PrimerTheme.stateInfo,
              foregroundColor: Colors.black,
              textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(PrimerTheme.radiusDefault)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScoreAndMetricsGrid(bool isLargeScreen) {
    final score = widget.viewModel.auditResult!.score;

    final heroCard = Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: PrimerTheme.surfaceCard,
        borderRadius: BorderRadius.circular(PrimerTheme.radiusDefault),
        border: Border.all(color: PrimerTheme.borderDefault),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.between,
            children: [
              const Text(
                'READINESS SCORE',
                style: TextStyle(color: PrimerTheme.textMuted, fontSize: 11, fontWeight: FontWeight.w600),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: PrimerTheme.stateV6.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(color: PrimerTheme.stateV6.withOpacity(0.35)),
                ),
                child: Text(
                  score.letterGrade,
                  style: const TextStyle(color: PrimerTheme.stateV6, fontSize: 11, fontWeight: FontWeight.w600),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '${score.scorePercent.toStringAsFixed(0)}%',
            style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, fontFamily: 'monospace', color: PrimerTheme.textPrimary),
          ),
          Text(
            score.verdict,
            style: const TextStyle(color: PrimerTheme.stateV6, fontSize: 13, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );

    final kpis = [
      MetricCard(
        label: 'Subresources',
        value: score.subresourceRatioString,
        subtitle: '${score.subresourcePercentage.toStringAsFixed(1)}% Dual-Stack',
        valueColor: PrimerTheme.textPrimary,
      ),
      MetricCard(
        label: 'Apex AAAA',
        value: score.apexHasAaaa ? 'PASS' : 'FAIL',
        subtitle: score.apexHasAaaa ? 'Verified AAAA' : 'Missing AAAA',
        valueColor: score.apexHasAaaa ? PrimerTheme.stateV6 : PrimerTheme.stateV4,
      ),
      MetricCard(
        label: 'Latency Delta',
        value: score.latencyDeltaMs != null ? '+${score.latencyDeltaMs!.toStringAsFixed(1)}ms' : '--',
        subtitle: 'AF_INET6 vs IPv4',
        valueColor: PrimerTheme.stateInfo,
      ),
    ];

    if (isLargeScreen) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(flex: 5, child: heroCard),
          const SizedBox(width: 16),
          Expanded(
            flex: 7,
            child: Row(
              children: kpis.map((kpi) => Expanded(child: Padding(padding: const EdgeInsets.symmetric(horizontal: 4), child: kpi))).toList(),
            ),
          ),
        ],
      );
    } else {
      return Column(
        children: [
          heroCard,
          const SizedBox(height: 12),
          ...kpis.map((kpi) => Padding(padding: const EdgeInsets.only(bottom: 8), child: kpi)),
        ],
      );
    }
  }

  Widget _buildTopologyCard() {
    final nodes = widget.viewModel.auditResult!.nodes;

    return Container(
      height: 340,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: PrimerTheme.surfaceCard,
        borderRadius: BorderRadius.circular(PrimerTheme.radiusDefault),
        border: Border.all(color: PrimerTheme.borderDefault),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.between,
            children: [
              const Text(
                'Dependency Mesh Topology',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: PrimerTheme.textPrimary),
              ),
              Text(
                '${nodes.length} Nodes',
                style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: PrimerTheme.textMuted),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: PrimerTheme.bgPage,
                borderRadius: BorderRadius.circular(PrimerTheme.radiusDefault),
                border: Border.all(color: PrimerTheme.borderMuted),
              ),
              child: CustomPaint(
                painter: TopologyMeshPainter(
                  nodes: nodes,
                  selectedNode: widget.viewModel.selectedNode,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInspectorDrawer() {
    final node = widget.viewModel.selectedNode;
    if (node == null) return const SizedBox();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: PrimerTheme.surfaceCard,
        borderRadius: BorderRadius.circular(PrimerTheme.radiusDefault),
        border: Border.all(color: PrimerTheme.borderDefault),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.between,
            children: [
              Expanded(
                child: Text(
                  node.host,
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: PrimerTheme.textPrimary),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              ProtocolBadge(status: node.status),
            ],
          ),
          const SizedBox(height: 12),
          const Divider(color: PrimerTheme.borderDefault, height: 1),
          const SizedBox(height: 12),
          const Text(
            'Actionable CLI Verification',
            style: TextStyle(color: PrimerTheme.stateInfo, fontSize: 11, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: PrimerTheme.surfaceSubdued,
              borderRadius: BorderRadius.circular(PrimerTheme.radiusDefault),
              border: Border.all(color: PrimerTheme.borderDefault),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    node.actionableCliCommand,
                    style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: PrimerTheme.stateInfo),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.copy, size: 14, color: PrimerTheme.textMuted),
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: node.actionableCliCommand));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Command copied to clipboard'), duration: Duration(seconds: 1)),
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: PrimerTheme.surfaceCard,
        borderRadius: BorderRadius.circular(PrimerTheme.radiusDefault),
        border: Border.all(color: PrimerTheme.borderDefault),
      ),
      child: const Center(
        child: Column(
          children: [
            Icon(Icons.radar, size: 36, color: PrimerTheme.textDim),
            SizedBox(height: 12),
            Text('Ready to Audit Endpoint', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
            SizedBox(height: 4),
            Text(
              'Enter a target URL above to test 4-stage OSI compliance and dependency readiness.',
              style: TextStyle(color: PrimerTheme.textMuted, fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
