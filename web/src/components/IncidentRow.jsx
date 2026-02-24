import { Link } from 'react-router-dom'
import { Box, Flex, Text, HStack, Code } from '@chakra-ui/react'
import SeverityBadge from './SeverityBadge'

function timeAgo(isoString) {
  const diff = Date.now() - new Date(isoString).getTime()
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return 'just now'
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

const hoverBorderMap = {
  P1: '#fecdd3',
  P2: '#fde68a',
  P3: '#bae6fd',
  P4: '#c7d2fe',
}

export default function IncidentRow({ incident }) {
  return (
    <Box
      as={Link}
      to={`/incidents/${incident.id}`}
      display="block"
      bg="white"
      border="1px solid"
      borderColor="#e2e5eb"
      borderRadius="xl"
      p={5}
      boxShadow="0 1px 3px rgba(0,0,0,0.04)"
      transition="all 0.2s"
      _hover={{
        bg: '#fafbfc',
        borderColor: hoverBorderMap[incident.severity] || '#cdd1d9',
        boxShadow: '0 3px 12px rgba(0,0,0,0.06)',
        textDecoration: 'none',
      }}
      role="group"
    >
      <Flex align="flex-start" gap={4}>
        {/* Left: severity */}
        <Box pt={0.5}>
          <SeverityBadge severity={incident.severity} dot />
        </Box>

        {/* Center: content */}
        <Box flex={1} minW={0}>
          <HStack spacing={2} mb={1}>
            <Code fontSize="11px" color="#9ca3b0" fontFamily="mono" bg="transparent" p={0}>
              {incident.id}
            </Code>
            <Text fontSize="11px" color="#d0d4dc">·</Text>
            <Text fontSize="11px" color="#9ca3b0">{timeAgo(incident.created_at)}</Text>
          </HStack>

          <Text
            fontSize="sm"
            color="#1a1d26"
            lineHeight="relaxed"
            fontWeight="medium"
            _groupHover={{ color: '#0e7490' }}
            transition="color 0.2s"
            noOfLines={2}
          >
            {incident.title}
          </Text>

          {incident.root_cause && (
            <Text fontSize="xs" color="#6b7280" mt={2} noOfLines={1} lineHeight="relaxed">
              <Text as="span" color="#9ca3b0">Root cause:</Text> {incident.root_cause}
            </Text>
          )}

          {/* Tags row */}
          <HStack spacing={2} mt={3} flexWrap="wrap">
            {incident.services.map(svc => (
              <Text
                key={svc}
                fontSize="11px"
                bg="#f1f3f6"
                color="#4a5068"
                px={2}
                py="2px"
                borderRadius="md"
                fontFamily="mono"
                border="1px solid"
                borderColor="#eceef2"
              >
                {svc}
              </Text>
            ))}
            <Text fontSize="11px" color="#d0d4dc">·</Text>
            <Text fontSize="11px" color="#9ca3b0">{incident.anomaly_count} anomalies</Text>
            {incident.has_analysis && (
              <>
                <Text fontSize="11px" color="#d0d4dc">·</Text>
                <HStack spacing={1} fontSize="11px" color="#7c3aed">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
                  </svg>
                  <Text fontWeight="medium">AI ({incident.confidence})</Text>
                </HStack>
              </>
            )}
          </HStack>
        </Box>

        {/* Right: arrow */}
        <Box
          mt={1}
          flexShrink={0}
          color="#d0d4dc"
          _groupHover={{ color: '#0891b2', transform: 'translateX(2px)' }}
          transition="all 0.2s"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </Box>
      </Flex>
    </Box>
  )
}
