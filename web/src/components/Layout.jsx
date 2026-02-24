import { Link, Outlet } from 'react-router-dom'
import { Box, Flex, Text, Container, HStack } from '@chakra-ui/react'
import { useApi } from '../hooks/useApi'

export default function Layout() {
  const { data: health } = useApi('/health', 15000)

  return (
    <Box minH="100vh" bg="#f8f9fb">
      {/* Nav */}
      <Box
        as="nav"
        borderBottom="1px solid"
        borderColor="#e2e5eb"
        bg="rgba(255, 255, 255, 0.85)"
        backdropFilter="blur(20px)"
        position="sticky"
        top={0}
        zIndex={50}
      >
        <Container maxW="1400px" px={6}>
          <Flex align="center" justify="space-between" h="64px">
            <Flex as={Link} to="/" align="center" gap={3} _hover={{ textDecoration: 'none' }}>
              <Box
                w={9}
                h={9}
                borderRadius="lg"
                bgGradient="linear(to-br, #0891b2, #0e7490)"
                display="flex"
                alignItems="center"
                justifyContent="center"
                boxShadow="0 2px 8px rgba(8, 145, 178, 0.25)"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" strokeWidth={2.2} stroke="white">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
              </Box>
              <Box>
                <Text fontSize="17px" fontWeight="bold" color="#1a1d26" letterSpacing="tight" lineHeight="short">
                  SentinelOps
                </Text>
                <Text display={{ base: 'none', sm: 'block' }} fontSize="11px" color="#9ca3b0" mt="-2px">
                  Incident Response Agent
                </Text>
              </Box>
            </Flex>

            <HStack spacing={5}>
              {health && (
                <HStack display={{ base: 'none', sm: 'flex' }} spacing={2} fontSize="xs" color="#6b7280">
                  <Text fontFamily="mono" color="#0891b2" fontWeight="semibold">{health.incidents_tracked}</Text>
                  <Text>incidents tracked</Text>
                </HStack>
              )}
              <HStack
                spacing={2}
                px={3}
                py={1.5}
                borderRadius="full"
                bg="#ecfdf5"
                border="1px solid"
                borderColor="#d1fae5"
              >
                <Box
                  h={2}
                  w={2}
                  borderRadius="full"
                  bg="#10b981"
                  boxShadow="0 0 6px rgba(16, 185, 129, 0.4)"
                  sx={{
                    animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                    '@keyframes pulse': {
                      '0%, 100%': { opacity: 1 },
                      '50%': { opacity: 0.4 },
                    },
                  }}
                />
                <Text fontSize="xs" fontWeight="semibold" color="#059669">
                  Live
                </Text>
              </HStack>
            </HStack>
          </Flex>
        </Container>
      </Box>

      {/* Content */}
      <Container as="main" maxW="1400px" px={6} py={8}>
        <Outlet />
      </Container>
    </Box>
  )
}
