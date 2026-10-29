import 'package:test/test.dart';
import '../../lib/domain/models/audit_score.dart';

void main() {
  group('AuditScore Domain Unit Tests', () {
    test('calculates subresourcePercentage correctly', () {
      const score = AuditScore(
        scorePercent: 85.0,
        verdict: 'Dual-Stack Ready',
        letterGrade: 'Grade A-',
        totalSubresources: 200,
        ipv6Subresources: 150,
        ipv4Subresources: 50,
        apexHasAaaa: true,
      );

      expect(score.subresourcePercentage, equals(75.0));
      expect(score.subresourceRatioString, equals('150 / 200'));
      expect(score.isPureIpv6Ready, isFalse);
    });

    test('isPureIpv6Ready is true only when score >= 95 and apexHasAaaa is true', () {
      const pureScore = AuditScore(
        scorePercent: 96.0,
        verdict: 'Pure IPv6 Ready',
        letterGrade: 'Grade A+',
        totalSubresources: 50,
        ipv6Subresources: 50,
        ipv4Subresources: 0,
        apexHasAaaa: true,
      );

      expect(pureScore.isPureIpv6Ready, isTrue);

      const noAaaaScore = AuditScore(
        scorePercent: 96.0,
        verdict: 'Missing AAAA',
        letterGrade: 'Grade F',
        totalSubresources: 50,
        ipv6Subresources: 50,
        ipv4Subresources: 0,
        apexHasAaaa: false,
      );

      expect(noAaaaScore.isPureIpv6Ready, isFalse);
    });

    test('calculates latencyDeltaMs accurately', () {
      const scoreWithLatency = AuditScore(
        scorePercent: 80.0,
        verdict: 'Dual-Stack',
        letterGrade: 'Grade A-',
        totalSubresources: 10,
        ipv6Subresources: 8,
        ipv4Subresources: 2,
        apexHasAaaa: true,
        ipv6TtfbMs: 25.5,
        ipv4TtfbMs: 20.0,
      );

      expect(scoreWithLatency.latencyDeltaMs, equals(5.5));
    });
  });
}
