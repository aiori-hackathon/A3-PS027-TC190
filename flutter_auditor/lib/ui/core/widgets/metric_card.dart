import 'package:flutter/material.dart';
import '../theme/primer_theme.dart';

class MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final String? subtitle;
  final Widget? trailingBadge;
  final Color? valueColor;

  const MetricCard({
    super.key,
    required this.label,
    required this.value,
    this.subtitle,
    this.trailingBadge,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: PrimerTheme.surfaceCard,
        borderRadius: BorderRadius.circular(PrimerTheme.radiusDefault),
        border: Border.all(color: PrimerTheme.borderDefault, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.between,
            children: [
              Text(
                label.toUpperCase(),
                style: const TextStyle(
                  color: PrimerTheme.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.5,
                ),
              ),
              if (trailingBadge != null) trailingBadge!,
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              color: valueColor ?? PrimerTheme.textPrimary,
              fontSize: 18,
              fontWeight: FontWeight.w700,
              fontFamily: 'monospace',
            ),
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 4),
            Text(
              subtitle!,
              style: const TextStyle(
                color: PrimerTheme.textMuted,
                fontSize: 12,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
