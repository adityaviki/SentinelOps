import { Box, Flex, Grid, GridItem, Text, VStack } from '@chakra-ui/react'
import { useApi } from '../hooks/useApi'
import StatsBar from '../components/StatsBar'
import ServiceCard from '../components/ServiceCard'
import IncidentRow from '../components/IncidentRow'

export default function Dashboard() {
  const { data: incData, loading: incLoading } = useApi('/incidents?limit=20', 10000)
  const { data: svcData, loading: svcLoading } = useApi('/services', 10000)

  return (
    <VStack spacing={8} align="stretch">
      {/* Stats Overview */}
      <StatsBar incidents={incData} services={svcData} />

      {/* Two-column layout */}
      <Grid templateColumns={{ base: '1fr', lg: '1fr 2fr' }} gap={8}>
        {/* Left: Service Health */}
        <GridItem>
          <Flex align="center" gap={2} mb={4}>
            <Box color="#0891b2">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 0 1-3-3m3 3a3 3 0 1 0 0 6h13.5a3 3 0 1 0 0-6m-16.5-3a3 3 0 0 1 3-3h13.5a3 3 0 0 1 3 3m-19.5 0a4.5 4.5 0 0 1 .9-2.7L5.737 5.1a3.375 3.375 0 0 1 2.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 0 1 .9 2.7m0 0a3 3 0 0 1-3 3m0 3h.008v.008h-.008v-.008Zm0-6h.008v.008h-.008v-.008Zm-3 6h.008v.008h-.008v-.008Zm0-6h.008v.008h-.008v-.008Z" />
              </svg>
            </Box>
            <Text fontSize="sm" fontWeight="semibold" color="#4a5068" textTransform="uppercase" letterSpacing="wider">
              Services
            </Text>
          </Flex>

          {svcLoading ? (
            <VStack spacing={3}>
              {[1, 2, 3].map(i => (
                <Box
                  key={i}
                  h="160px"
                  borderRadius="xl"
                  border="1px solid"
                  borderColor="#eceef2"
                  bg="#f1f3f6"
                  className="animate-pulse"
                  w="full"
                />
              ))}
            </VStack>
          ) : svcData?.services.length > 0 ? (
            <VStack spacing={3}>
              {svcData.services.map((svc) => (
                <Box key={svc.service} w="full">
                  <ServiceCard service={svc} />
                </Box>
              ))}
            </VStack>
          ) : (
            <EmptyState
              icon={
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" strokeWidth={1} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
                </svg>
              }
              title="No services detected"
              subtitle="Services will appear once anomalies are found."
            />
          )}
        </GridItem>

        {/* Right: Incidents Feed */}
        <GridItem>
          <Flex align="center" justify="space-between" mb={4}>
            <Flex align="center" gap={2}>
              <Box color="#0891b2">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
              </Box>
              <Text fontSize="sm" fontWeight="semibold" color="#4a5068" textTransform="uppercase" letterSpacing="wider">
                Incidents
              </Text>
            </Flex>
            {incData?.total > 0 && (
              <Text fontSize="11px" color="#9ca3b0" fontVariantNumeric="tabular-nums">{incData.total} total</Text>
            )}
          </Flex>

          {incLoading ? (
            <VStack spacing={3}>
              {[1, 2, 3].map(i => (
                <Box
                  key={i}
                  h="128px"
                  borderRadius="xl"
                  border="1px solid"
                  borderColor="#eceef2"
                  bg="#f1f3f6"
                  className="animate-pulse"
                  w="full"
                />
              ))}
            </VStack>
          ) : incData?.incidents.length > 0 ? (
            <VStack spacing={3}>
              {incData.incidents.map((inc) => (
                <Box key={inc.id} w="full">
                  <IncidentRow incident={inc} />
                </Box>
              ))}
            </VStack>
          ) : (
            <EmptyState
              icon={
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" strokeWidth={0.8} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
                </svg>
              }
              title="All clear"
              subtitle="No incidents detected. SentinelOps is monitoring your services."
              large
            />
          )}
        </GridItem>
      </Grid>
    </VStack>
  )
}

function EmptyState({ icon, title, subtitle, large }) {
  return (
    <Flex
      direction="column"
      align="center"
      justify="center"
      textAlign="center"
      border="1px dashed"
      borderColor="#d0d4dc"
      borderRadius="xl"
      py={large ? 20 : 12}
      bg="white"
    >
      <Box color="#d0d4dc" mb={3}>{icon}</Box>
      <Text fontSize="sm" color="#6b7280" fontWeight="medium">{title}</Text>
      <Text fontSize="xs" color="#9ca3b0" mt={1}>{subtitle}</Text>
    </Flex>
  )
}
