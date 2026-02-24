import { useParams, Link } from 'react-router-dom'
import { Box, Flex, Text, HStack, Code } from '@chakra-ui/react'
import { useApi } from '../hooks/useApi'
import SeverityBadge from '../components/SeverityBadge'

function Section({ title, icon, count, children }) {
  return (
    <Box
      bg="white"
      border="1px solid"
      borderColor="#e2e5eb"
      borderRadius="xl"
      overflow="hidden"
      boxShadow="0 1px 3px rgba(0,0,0,0.04)"
    >
      <Flex
        px={5}
        py={3.5}
        bg="#fafbfc"
        borderBottom="1px solid"
        borderColor="#eceef2"
        align="center"
        gap={2}
      >
        {icon}
        <Text fontSize="sm" fontWeight="semibold" color="#1a1d26">
          {title}
        </Text>
        {count != null && (
          <Text fontSize="11px" color="#9ca3b0" ml="auto" fontVariantNumeric="tabular-nums">
            {count}
          </Text>
        )}
      </Flex>
      {children}
    </Box>
  )
}

export default function IncidentDetail() {
  const { id } = useParams()
  const { data: incident, loading, error } = useApi(`/incidents/${id}`)

  if (loading) {
    return (
      <Flex direction="column" gap={4} maxW="4xl" mx="auto">
        {[32, 48, 80, 64].map((h, i) => (
          <Box
            key={i}
            h={`${h * 4}px`}
            borderRadius="xl"
            border="1px solid"
            borderColor="#eceef2"
            bg="#f1f3f6"
            className="animate-pulse"
          />
        ))}
      </Flex>
    )
  }

  if (error || !incident) {
    return (
      <Flex direction="column" align="center" py={24}>
        <Box color="#d0d4dc" mb={3}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" strokeWidth={1} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        </Box>
        <Text color="#4a5068" fontSize="sm" fontWeight="medium">Incident not found</Text>
        <Text
          as={Link}
          to="/"
          fontSize="sm"
          color="#0891b2"
          _hover={{ color: '#0e7490' }}
          mt={3}
          transition="color 0.2s"
        >
          Back to Dashboard
        </Text>
      </Flex>
    )
  }

  return (
    <Flex direction="column" maxW="4xl" mx="auto" gap={5}>
      {/* Back */}
      <Flex
        as={Link}
        to="/"
        align="center"
        gap={1.5}
        fontSize="sm"
        color="#6b7280"
        _hover={{ color: '#0891b2', textDecoration: 'none' }}
        transition="color 0.2s"
        role="group"
        w="fit-content"
      >
        <Box _groupHover={{ transform: 'translateX(-2px)' }} transition="transform 0.2s">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
        </Box>
        Dashboard
      </Flex>

      {/* Header */}
      <Box
        bg="white"
        border="1px solid"
        borderColor="#e2e5eb"
        borderRadius="xl"
        p={6}
        boxShadow="0 1px 3px rgba(0,0,0,0.04)"
      >
        <HStack flexWrap="wrap" spacing={2.5} mb={3}>
          <SeverityBadge severity={incident.severity} size="lg" dot />
          <Code fontSize="xs" color="#9ca3b0" fontFamily="mono" bg="transparent" p={0}>
            {incident.id}
          </Code>
          <Text fontSize="xs" color="#d0d4dc">·</Text>
          <Text fontSize="xs" color="#6b7280">
            {new Date(incident.created_at).toLocaleString()}
          </Text>
        </HStack>
        <Text fontSize={{ base: 'md', sm: 'lg' }} fontWeight="semibold" color="#1a1d26" lineHeight="relaxed">
          {incident.title}
        </Text>
        <HStack flexWrap="wrap" spacing={1.5} mt={4}>
          {incident.services.map(svc => (
            <Text
              key={svc}
              fontSize="xs"
              bg="#f1f3f6"
              color="#4a5068"
              px={2.5}
              py={1}
              borderRadius="md"
              fontFamily="mono"
              border="1px solid"
              borderColor="#eceef2"
            >
              {svc}
            </Text>
          ))}
        </HStack>
      </Box>

      {/* AI Analysis */}
      {incident.analysis && (
        <Box
          borderRadius="xl"
          border="1px solid"
          borderColor="#ddd6fe"
          bg="#faf5ff"
          overflow="hidden"
          boxShadow="0 1px 4px rgba(124, 58, 237, 0.06)"
        >
          <Flex
            px={5}
            py={3.5}
            borderBottom="1px solid"
            borderColor="#ede9fe"
            align="center"
            gap={2}
            bg="#f5f3ff"
          >
            <Box color="#7c3aed">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
              </svg>
            </Box>
            <Text fontSize="sm" fontWeight="semibold" color="#6d28d9">AI Analysis</Text>
            <Text
              ml="auto"
              fontSize="11px"
              bg="white"
              color="#7c3aed"
              px={2.5}
              py={0.5}
              borderRadius="full"
              fontWeight="semibold"
              border="1px solid"
              borderColor="#ddd6fe"
            >
              {incident.analysis.confidence} confidence
            </Text>
          </Flex>
          <Flex direction="column" p={5} gap={5}>
            <Box>
              <Text fontSize="11px" fontWeight="semibold" color="#9ca3b0" textTransform="uppercase" letterSpacing="wider" mb={2}>
                Root Cause
              </Text>
              <Text fontSize="sm" color="#4a5068" lineHeight="relaxed">{incident.analysis.root_cause}</Text>
            </Box>
            <Box>
              <Text fontSize="11px" fontWeight="semibold" color="#9ca3b0" textTransform="uppercase" letterSpacing="wider" mb={3}>
                Remediation Steps
              </Text>
              <Flex direction="column" gap={2.5}>
                {incident.analysis.remediation_steps.map((step, i) => (
                  <Flex key={i} align="flex-start" gap={3} fontSize="sm" color="#4a5068" lineHeight="relaxed">
                    <Flex
                      flexShrink={0}
                      w={6}
                      h={6}
                      borderRadius="lg"
                      bg="#f5f3ff"
                      color="#7c3aed"
                      fontSize="xs"
                      align="center"
                      justify="center"
                      fontWeight="bold"
                      mt={0.5}
                      border="1px solid"
                      borderColor="#ddd6fe"
                    >
                      {i + 1}
                    </Flex>
                    <Text>{step}</Text>
                  </Flex>
                ))}
              </Flex>
            </Box>
          </Flex>
        </Box>
      )}

      {/* Anomalies */}
      <Section
        title="Anomalies"
        count={incident.anomalies.length}
        icon={
          <Box color="#0891b2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
          </Box>
        }
      >
        <Box>
          {incident.anomalies.map((a, i) => {
            const ratio = a.baseline_mean > 0 ? (a.current_value / a.baseline_mean) : 0
            return (
              <Flex
                key={i}
                px={5}
                py={3.5}
                align="center"
                justify="space-between"
                gap={4}
                borderBottom={i < incident.anomalies.length - 1 ? '1px solid' : 'none'}
                borderColor="#eceef2"
                _hover={{ bg: '#fafbfc' }}
                transition="background 0.15s"
              >
                <Flex align="center" gap={3} minW={0}>
                  <SeverityBadge severity={a.severity} />
                  <Box minW={0}>
                    <Text as="span" fontSize="sm" color="#1a1d26" fontWeight="medium">{a.service}</Text>
                    <Text as="span" fontSize="xs" fontFamily="mono" color="#9ca3b0" ml={2}>{a.metric}</Text>
                  </Box>
                </Flex>
                <Flex align="center" gap={5} fontSize="xs" flexShrink={0}>
                  <Box textAlign="right">
                    <Text color="#1a1d26" fontWeight="semibold" fontVariantNumeric="tabular-nums">{a.current_value.toFixed(1)}</Text>
                    <Text color="#9ca3b0" fontVariantNumeric="tabular-nums">baseline {a.baseline_mean.toFixed(1)}</Text>
                  </Box>
                  <Box w={16} textAlign="right">
                    <Text fontFamily="mono" fontWeight="bold" color="#b45309" fontVariantNumeric="tabular-nums">
                      z={a.z_score.toFixed(1)}
                    </Text>
                    {ratio > 1 && (
                      <Text fontSize="10px" color="#9ca3b0" fontVariantNumeric="tabular-nums">{ratio.toFixed(0)}x</Text>
                    )}
                  </Box>
                </Flex>
              </Flex>
            )
          })}
        </Box>
      </Section>

      {/* Correlated Events */}
      {incident.correlated_events?.length > 0 && (
        <Section
          title="Correlated Events"
          count={incident.correlated_events.length}
          icon={
            <Box color="#0891b2">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
              </svg>
            </Box>
          }
        >
          <Box maxH="420px" overflowY="auto">
            {incident.correlated_events.map((e, i) => (
              <Box
                key={i}
                px={5}
                py={3}
                borderBottom={i < incident.correlated_events.length - 1 ? '1px solid' : 'none'}
                borderColor="#eceef2"
                _hover={{ bg: '#fafbfc' }}
                transition="background 0.15s"
              >
                <Flex align="center" gap={2} mb={1}>
                  <Text
                    fontSize="11px"
                    fontWeight="bold"
                    textTransform="uppercase"
                    letterSpacing="wider"
                    color={e.level === 'error' ? '#be123c' : '#b45309'}
                    bg={e.level === 'error' ? '#fff1f3' : '#fffbeb'}
                    px={1.5}
                    py="1px"
                    borderRadius="sm"
                  >
                    {e.level}
                  </Text>
                  <Text fontSize="xs" fontWeight="medium" color="#1a1d26">{e.service}</Text>
                  {e.trace_id && (
                    <Code fontSize="10px" color="#b8bec9" fontFamily="mono" ml="auto" bg="transparent" p={0}>
                      {e.trace_id.slice(0, 16)}
                    </Code>
                  )}
                  <Text fontSize="11px" color="#9ca3b0" fontVariantNumeric="tabular-nums">
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </Text>
                </Flex>
                <Text fontSize="xs" color="#6b7280" lineHeight="relaxed">{e.message}</Text>
              </Box>
            ))}
          </Box>
        </Section>
      )}

      {/* Matched Runbooks */}
      {incident.matched_runbooks?.length > 0 && (
        <Section
          title="Matched Runbooks"
          count={incident.matched_runbooks.length}
          icon={
            <Box color="#0891b2">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
              </svg>
            </Box>
          }
        >
          <Box>
            {incident.matched_runbooks.map((rb, i) => (
              <Box
                key={i}
                px={5}
                py={4}
                borderBottom={i < incident.matched_runbooks.length - 1 ? '1px solid' : 'none'}
                borderColor="#eceef2"
              >
                <Flex align="flex-start" justify="space-between" gap={2} mb={2}>
                  <Text fontSize="sm" fontWeight="semibold" color="#1a1d26">{rb.title}</Text>
                  {rb.services_affected?.length > 0 && (
                    <HStack spacing={1} flexShrink={0}>
                      {rb.services_affected.map(s => (
                        <Text key={s} fontSize="10px" bg="#f1f3f6" color="#6b7280" px={1.5} py="2px" borderRadius="sm" fontFamily="mono">
                          {s}
                        </Text>
                      ))}
                    </HStack>
                  )}
                </Flex>
                {rb.root_cause && (
                  <Text fontSize="xs" color="#6b7280" mb={3} lineHeight="relaxed">{rb.root_cause}</Text>
                )}
                {rb.resolution_steps?.length > 0 && (
                  <Flex direction="column" gap={1}>
                    {rb.resolution_steps.map((step, j) => (
                      <Flex key={j} align="flex-start" gap={2} fontSize="xs" color="#6b7280">
                        <Text color="#0891b2" fontFamily="mono" fontWeight="semibold" flexShrink={0}>{j + 1}.</Text>
                        <Text>{step}</Text>
                      </Flex>
                    ))}
                  </Flex>
                )}
              </Box>
            ))}
          </Box>
        </Section>
      )}
    </Flex>
  )
}
