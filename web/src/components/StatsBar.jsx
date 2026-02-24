import { Box, Flex, Grid, Text } from '@chakra-ui/react'

export default function StatsBar({ incidents, services }) {
  const totalIncidents = incidents?.total || 0
  const criticalServices = services?.services?.filter(s => s.status === 'critical').length || 0
  const totalServices = services?.services?.length || 0
  const hasAnalysis = incidents?.incidents?.filter(i => i.has_analysis).length || 0

  const stats = [
    {
      label: 'Active Incidents',
      value: totalIncidents,
      color: totalIncidents > 0 ? '#be123c' : '#059669',
      iconBg: totalIncidents > 0 ? '#fff1f3' : '#ecfdf5',
      iconBorder: totalIncidents > 0 ? '#fecdd3' : '#d1fae5',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" strokeWidth={1.8} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
      ),
    },
    {
      label: 'Critical Services',
      value: `${criticalServices}/${totalServices}`,
      color: criticalServices > 0 ? '#b45309' : '#059669',
      iconBg: criticalServices > 0 ? '#fffbeb' : '#ecfdf5',
      iconBorder: criticalServices > 0 ? '#fde68a' : '#d1fae5',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" strokeWidth={1.8} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 0 1-3-3m3 3a3 3 0 1 0 0 6h13.5a3 3 0 1 0 0-6m-16.5-3a3 3 0 0 1 3-3h13.5a3 3 0 0 1 3 3m-19.5 0a4.5 4.5 0 0 1 .9-2.7L5.737 5.1a3.375 3.375 0 0 1 2.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 0 1 .9 2.7m0 0a3 3 0 0 1-3 3m0 3h.008v.008h-.008v-.008Zm0-6h.008v.008h-.008v-.008Zm-3 6h.008v.008h-.008v-.008Zm0-6h.008v.008h-.008v-.008Z" />
        </svg>
      ),
    },
    {
      label: 'AI Analyzed',
      value: hasAnalysis,
      color: '#7c3aed',
      iconBg: '#f5f3ff',
      iconBorder: '#ddd6fe',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" strokeWidth={1.8} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
        </svg>
      ),
    },
  ]

  return (
    <Grid templateColumns={{ base: '1fr', sm: 'repeat(3, 1fr)' }} gap={4}>
      {stats.map((stat) => (
        <Flex
          key={stat.label}
          px={5}
          py={4}
          align="center"
          gap={4}
          bg="white"
          border="1px solid"
          borderColor="#e2e5eb"
          borderRadius="xl"
          boxShadow="0 1px 3px rgba(0,0,0,0.04)"
          transition="all 0.2s"
          _hover={{ boxShadow: '0 2px 8px rgba(0,0,0,0.06)', borderColor: '#cdd1d9' }}
        >
          <Flex
            p={2.5}
            borderRadius="lg"
            bg={stat.iconBg}
            border="1px solid"
            borderColor={stat.iconBorder}
            color={stat.color}
            align="center"
            justify="center"
          >
            {stat.icon}
          </Flex>
          <Box>
            <Text fontSize="2xl" fontWeight="bold" color={stat.color} fontVariantNumeric="tabular-nums">
              {stat.value}
            </Text>
            <Text fontSize="xs" color="#6b7280" mt={0.5}>
              {stat.label}
            </Text>
          </Box>
        </Flex>
      ))}
    </Grid>
  )
}
