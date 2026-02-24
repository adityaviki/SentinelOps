import { Box, HStack } from '@chakra-ui/react'

const styles = {
  P1: {
    bg: '#fff1f3',
    color: '#be123c',
    borderColor: '#fecdd3',
    dotBg: '#e11d48',
  },
  P2: {
    bg: '#fffbeb',
    color: '#b45309',
    borderColor: '#fde68a',
    dotBg: '#d97706',
  },
  P3: {
    bg: '#f0f9ff',
    color: '#0369a1',
    borderColor: '#bae6fd',
    dotBg: '#0284c7',
  },
  P4: {
    bg: '#eef2ff',
    color: '#4f46e5',
    borderColor: '#c7d2fe',
    dotBg: '#6366f1',
  },
}

const sizeMap = {
  sm: { px: 2, py: '2px', fontSize: '11px', gap: 1 },
  md: { px: 2.5, py: '2px', fontSize: 'xs', gap: 1.5 },
  lg: { px: 3, py: 1, fontSize: 'sm', gap: 2 },
}

export default function SeverityBadge({ severity, size = 'sm', dot = false }) {
  const s = styles[severity] || styles.P4
  const sz = sizeMap[size] || sizeMap.sm

  return (
    <HStack
      as="span"
      display="inline-flex"
      spacing={sz.gap}
      px={sz.px}
      py={sz.py}
      fontSize={sz.fontSize}
      fontWeight="bold"
      borderRadius="md"
      bg={s.bg}
      color={s.color}
      border="1px solid"
      borderColor={s.borderColor}
      textTransform="none"
    >
      {dot && <Box w="6px" h="6px" borderRadius="full" bg={s.dotBg} />}
      <span>{severity}</span>
    </HStack>
  )
}
