import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../../lib/ui/core/widgets/metric_card.dart';
import '../../lib/ui/core/theme/primer_theme.dart';

void main() {
  group('MetricCard Widget Tests', () {
    testWidgets('renders label, value, and subtitle correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: MetricCard(
              label: 'Subresources',
              value: '142 / 168',
              subtitle: '84.5% Dual-Stack',
              valueColor: PrimerTheme.stateV6,
            ),
          ),
        ),
      );

      // Verify label rendered in uppercase
      expect(find.text('SUBRESOURCES'), findsOneWidget);

      // Verify value rendered
      expect(find.text('142 / 168'), findsOneWidget);

      // Verify subtitle rendered
      expect(find.text('84.5% Dual-Stack'), findsOneWidget);
    });

    testWidgets('renders trailing badge widget when provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: MetricCard(
              label: 'Apex AAAA',
              value: 'PASS',
              trailingBadge: Chip(label: Text('RFC 3596')),
            ),
          ),
        ),
      );

      expect(find.text('APEX AAAA'), findsOneWidget);
      expect(find.text('PASS'), findsOneWidget);
      expect(find.text('RFC 3596'), findsOneWidget);
    });
  });
}
