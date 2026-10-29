import 'package:flutter/material.dart';
import '../theme/primer_theme.dart';
import 'metric_card.dart';
import 'protocol_badge.dart';
import '../../domain/models/dependency_node.dart';

/// Previews for MetricCard adhering to flutter-add-widget-preview
Widget buildMetricCardPreview() {
  return MaterialApp(
    theme: PrimerTheme.darkTheme,
    home: const Scaffold(
      backgroundColor: PrimerTheme.bgPage,
      body: Center(
        child: SizedBox(
          width: 260,
          child: MetricCard(
            label: 'Apex AAAA Record',
            value: 'PASS',
            subtitle: '2606:50c0:8000::153',
            valueColor: PrimerTheme.stateV6,
            trailingBadge: ProtocolBadge(
              status: ProtocolStatus.ipv6Ready,
              customLabel: 'RFC 3596',
            ),
          ),
        ),
      ),
    ),
  );
}
