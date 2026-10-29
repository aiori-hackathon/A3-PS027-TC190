import 'dart:math';
import 'package:flutter/material.dart';
import '../../../../domain/models/dependency_node.dart';
import '../../../core/theme/primer_theme.dart';

class TopologyMeshPainter extends CustomPainter {
  final List<DependencyNode> nodes;
  final DependencyNode? selectedNode;

  TopologyMeshPainter({
    required this.nodes,
    this.selectedNode,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (nodes.isEmpty) return;

    final center = Offset(size.width / 2, size.height / 2);
    final count = nodes.length - 1;
    final radius = min(size.width, size.height) * 0.38;

    final linePaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    final nodePaint = Paint()..style = PaintingStyle.fill;

    // 1. Draw edge curves from apex to dependencies
    for (int i = 1; i < nodes.length; i++) {
      final angle = (i - 1) * (2 * pi / max(1, count));
      final nodePos = Offset(
        center.dx + cos(angle) * radius,
        center.dy + sin(angle) * (radius * 0.75),
      );

      final node = nodes[i];
      if (node.status == ProtocolStatus.ipv6Ready) {
        linePaint.color = PrimerTheme.stateV6.withOpacity(0.35);
      } else if (node.status == ProtocolStatus.brokenRoute) {
        linePaint.color = PrimerTheme.stateBroken.withOpacity(0.35);
      } else {
        linePaint.color = PrimerTheme.stateV4.withOpacity(0.35);
      }

      final path = Path()
        ..moveTo(center.dx, center.dy)
        ..quadraticBezierTo(
          center.dx + (nodePos.dx - center.dx) * 0.5,
          center.dy,
          nodePos.dx,
          nodePos.dy,
        );
      canvas.drawPath(path, linePaint);
    }

    // 2. Draw leaf nodes
    for (int i = 1; i < nodes.length; i++) {
      final angle = (i - 1) * (2 * pi / max(1, count));
      final nodePos = Offset(
        center.dx + cos(angle) * radius,
        center.dy + sin(angle) * (radius * 0.75),
      );

      final node = nodes[i];
      if (node.status == ProtocolStatus.ipv6Ready) {
        nodePaint.color = PrimerTheme.stateV6;
      } else if (node.status == ProtocolStatus.brokenRoute) {
        nodePaint.color = PrimerTheme.stateBroken;
      } else {
        nodePaint.color = PrimerTheme.stateV4;
      }

      canvas.drawCircle(nodePos, 6, nodePaint);

      if (node == selectedNode) {
        final ringPaint = Paint()
          ..color = PrimerTheme.stateInfo
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.0;
        canvas.drawCircle(nodePos, 10, ringPaint);
      }
    }

    // 3. Draw Apex root node at center
    final apexNode = nodes.first;
    nodePaint.color = PrimerTheme.surfaceCard;
    canvas.drawCircle(center, 18, nodePaint);

    final apexBorderPaint = Paint()
      ..color = PrimerTheme.stateInfo
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    canvas.drawCircle(center, 18, apexBorderPaint);

    nodePaint.color = PrimerTheme.stateInfo;
    canvas.drawCircle(center, 6, nodePaint);
  }

  @override
  bool shouldRepaint(covariant TopologyMeshPainter oldDelegate) {
    return oldDelegate.nodes != nodes || oldDelegate.selectedNode != selectedNode;
  }
}
