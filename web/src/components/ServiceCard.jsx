import { Box, Flex, Text } from '@chakra-ui/react'
import SeverityBadge from './SeverityBadge'

const statusConfig = {
  critical: {
    borderColor: '#fecdd3',
    bg: 'linear-gradient(135deg, rgba(225, 29, 72, 0.04) 0%, transparent 60%)',
    bgColor: 'white',
    dotBg: '#e11d48',
    dotShadow: '0 0 6px rgba(225, 29, 72, 0.35)',
    label: 'Critical',
    labelColor: '#be123c',
    labelBg: '#fff1f3',
  },
  warning: {
    borderColor: '#fde68a',
    bg: 'linear-gradient(135deg, rgba(217, 119, 6, 0.04) 0%, transparent 60%)',
    bgColor: 'white',
    dotBg: '#d97706',
    dotShadow: '0 0 6px rgba(217, 119, 6, 0.35)',
    label: 'Warning',
    labelColor: '#b45309',
    labelBg: '#fffbeb',
  },
  degraded: {
    borderColor: '#bae6fd',
    bg: 'linear-gradient(135deg, rgba(2, 132, 199, 0.04) 0%, transparent 60%)',
    bgColor: 'white',
    dotBg: '#0284c7',
    dotShadow: '0 0 6px rgba(2, 132, 199, 0.35)',
    label: 'Degraded',
    labelColor: '#0369a1',
    labelBg: '#f0f9ff',
  },
  healthy: {
    borderColor: '#e2e5eb',
    bg: 'none',
    bgColor: 'white',
    dotBg: '#10b981',
    dotShadow: '0 0 6px rgba(16, 185, 129, 0.35)',
    label: 'Healthy',
    labelColor: '#059669',
    labelBg: '#ecfdf5',
  },
}

function MetricBar({ label, zScore, max = 50 }) {
  const pct = Math.min((zScore / max) * 100, 100)
  const barColor = zScore >= 5
    ? 'linear-gradient(90deg, #e11d48, #fb7185)'
    : zScore >= 3
    ? 'linear-gradient(90deg, #d97706, #fbbf24)'
    : 'linear-gradient(90deg, #0284c7, #38bdf8)'

  return (
    <Box>
      <Flex justify="space-between" fontSize="11px" mb={1}>
        <Text color="#6b7280" fontFamily="mono">{label}</Text>
        <Text color="#4a5068" fontVariantNumeric="tabular-nums" fontWeight="semibold">z={zScore.toFixed(1)}</Text>
      </Flex>
      <Box h="5px" bg="#f1f3f6" borderRadius="full" overflow="hidden">
        <Box
          h="full"
          borderRadius="full"
          bgImage={barColor}
          transition="all 0.5s"
          w={`${pct}%`}
        />
      </Box>
    </Box>
  )
}

export default function ServiceCard({ service }) {
  const cfg = statusConfig[service.status] || statusConfig.healthy

  const metricMap = {}
  for (const a of service.anomalies || []) {
    if (!metricMap[a.metric] || a.z_score > metricMap[a.metric].z_score) {
      metricMap[a.metric] = a
    }
  }
  const uniqueAnomalies = Object.values(metricMap)

  return (
    <Box
      borderRadius="xl"
      border="1px solid"
      borderColor={cfg.borderColor}
      bgImage={cfg.bg}
      bgColor={cfg.bgColor}
      p={4}
      boxShadow="0 1px 3px rgba(0,0,0,0.04)"
      transition="all 0.2s"
      _hover={{ boxShadow: '0 3px 12px rgba(0,0,0,0.06)' }}
    >
      <Flex align="center" justify="space-between" mb={4}>
        <Flex align="center" gap={2.5}>
          <Box
            w={2}
            h={2}
            borderRadius="full"
            bg={cfg.dotBg}
            boxShadow={cfg.dotShadow}
          />
          <Text fontWeight="semibold" color="#1a1d26" fontSize="13px">{service.service}</Text>
        </Flex>
        <Text
          fontSize="11px"
          fontWeight="semibold"
          color={cfg.labelColor}
          bg={cfg.labelBg}
          px={2}
          py="1px"
          borderRadius="full"
        >
          {cfg.label}
        </Text>
      </Flex>

      {uniqueAnomalies.length > 0 && (
        <Box mb={4}>
          <Flex direction="column" gap={2.5}>
            {uniqueAnomalies.map((a, i) => (
              <MetricBar key={i} label={a.metric} zScore={a.z_score} />
            ))}
          </Flex>
        </Box>
      )}

      <Flex
        align="center"
        justify="space-between"
        pt={3}
        borderTop="1px solid"
        borderColor="#eceef2"
      >
        <SeverityBadge severity={service.worst_severity} />
        <Text fontSize="11px" color="#9ca3b0" fontVariantNumeric="tabular-nums">
          {service.incident_count} incident{service.incident_count !== 1 ? 's' : ''}
        </Text>
      </Flex>
    </Box>
  )
}
