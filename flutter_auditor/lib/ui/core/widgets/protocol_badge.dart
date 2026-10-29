import 'package:flutter/material.dart';
import '../../domain/models/dependency_node.dart';
import '../theme/primer_theme.dart';

class ProtocolBadge extends StatelessWidget {
  final ProtocolStatus status;
  final String? customLabel;

  const ProtocolBadge({
    super.key,
    required this.status,
    this.customLabel,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color border;
    Color text;
    String label = customLabel ?? '';

    switch (status) {
      case ProtocolStatus.ipv6Ready:
        bg = PrimerTheme.stateV6.withOpacity(0.15);
        border = PrimerTheme.stateV6.withOpacity(0.35);
        text = PrimerTheme.stateV6;
        if (label.isEmpty) label = 'IPv6 Ready';
        break;
      case ProtocolStatus.ipv4Only:
        bg = PrimerTheme.stateV4.withOpacity(0.15);
        border = PrimerTheme.stateV4.withOpacity(0.35);
        text = PrimerTheme.stateV4;
        if (label.isEmpty) label = 'IPv4 Only';
        break;
      case ProtocolStatus.brokenRoute:
        bg = PrimerTheme.stateBroken.withOpacity(0.15);
        border = PrimerTheme.stateBroken.withOpacity(0.35);
        text = PrimerTheme.stateBroken;
        if (label.isEmpty) label = 'Broken Route';
        break;
      case ProtocolStatus.ipv4Literal:
        bg = PrimerTheme.stateV4.withOpacity(0.15);
        border = PrimerTheme.stateV4.withOpacity(0.35);
        text = PrimerTheme.stateV4;
        if (label.isEmpty) label = 'RFC 6052 Literal';
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: border, width: 1),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: text,
          fontSize: 11,
          fontWeight: FontWeight.w600,
          fontFamily: 'monospace',
        ),
      ),
    );
  }
}
