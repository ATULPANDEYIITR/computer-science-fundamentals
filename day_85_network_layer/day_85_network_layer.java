import java.math.BigInteger;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/*
 * Network Layer Engineering
 *
 * Enterprise network management model:
 * IPv4, IPv6, CIDR, subnet calculations,
 * interfaces, routing and longest-prefix matching.
 *
 * Java 17, standard library only.
 */

public class NetworkLayer {

    enum AddressFamily {
        IPV4(32),
        IPV6(128);

        private final int bits;

        AddressFamily(int bits) {
            this.bits = bits;
        }

        public int bits() {
            return bits;
        }
    }

    enum InterfaceState {
        UP,
        DOWN
    }

    enum RouteState {
        ACTIVE,
        INACTIVE
    }

    static class NetworkException extends RuntimeException {
        NetworkException(String message) {
            super(message);
        }
    }

    record IpAddress(
        String value,
        AddressFamily family,
        BigInteger numericValue
    ) {
        IpAddress {
            Objects.requireNonNull(value);
            Objects.requireNonNull(family);
            Objects.requireNonNull(numericValue);
        }

        static IpAddress parse(String input) {
            if (input == null || input.isBlank() ||
                input.contains("%")) {
                throw new NetworkException("Invalid IP address");
            }

            try {
                InetAddress parsed = InetAddress.getByName(input);

                byte[] bytes = parsed.getAddress();

                AddressFamily family = bytes.length == 4
                    ? AddressFamily.IPV4
                    : AddressFamily.IPV6;

                // BigInteger with positive sign preserves unsigned IP values.
                BigInteger numeric = new BigInteger(1, bytes);

                return new IpAddress(
                    parsed.getHostAddress().toLowerCase(),
                    family,
                    numeric
                );

            } catch (UnknownHostException exception) {
                throw new NetworkException(
                    "Invalid IP address: " + input
                );
            }
        }
    }

    record CidrNetwork(
        IpAddress address,
        int prefix,
        BigInteger network,
        BigInteger broadcast,
        BigInteger mask
    ) {
        CidrNetwork {
            Objects.requireNonNull(address);

            if (prefix < 0 || prefix > address.family().bits()) {
                throw new NetworkException("Invalid prefix length");
            }

            BigInteger fullMask = BigInteger.ONE
                .shiftLeft(address.family().bits())
                .subtract(BigInteger.ONE);

            BigInteger calculatedMask = prefix == 0
                ? BigInteger.ZERO
                : fullMask.shiftRight(
                    address.family().bits() - prefix
                ).shiftLeft(
                    address.family().bits() - prefix
                );

            BigInteger calculatedNetwork =
                address.numericValue().and(calculatedMask);

            BigInteger calculatedBroadcast =
                calculatedNetwork.or(fullMask.xor(calculatedMask));

            if (!calculatedNetwork.equals(network) ||
                !calculatedBroadcast.equals(broadcast) ||
                !calculatedMask.equals(mask)) {
                throw new NetworkException("Invalid network representation");
            }
        }

        static CidrNetwork parse(String cidr) {
            if (cidr == null) {
                throw new NetworkException("CIDR is required");
            }

            String[] parts = cidr.split("/", -1);

            if (parts.length != 2 ||
                !parts[1].matches("\\d+")) {
                throw new NetworkException("Malformed CIDR");
            }

            IpAddress address = IpAddress.parse(parts[0]);
            int prefix = Integer.parseInt(parts[1]);

            if (prefix < 0 || prefix > address.family().bits()) {
                throw new NetworkException("Prefix outside valid range");
            }

            BigInteger fullMask = BigInteger.ONE
                .shiftLeft(address.family().bits())
                .subtract(BigInteger.ONE);

            BigInteger mask = prefix == 0
                ? BigInteger.ZERO
                : fullMask.shiftRight(
                    address.family().bits() - prefix
                ).shiftLeft(
                    address.family().bits() - prefix
                );

            BigInteger network = address.numericValue().and(mask);

            if (!network.equals(address.numericValue())) {
                throw new NetworkException(
                    "CIDR contains host bits; provide a network address"
                );
            }

            BigInteger broadcast =
                network.or(fullMask.xor(mask));

            return new CidrNetwork(
                address,
                prefix,
                network,
                broadcast,
                mask
            );
        }

        BigInteger totalAddresses() {
            return BigInteger.ONE.shiftLeft(
                address.family().bits() - prefix
            );
        }

        boolean contains(IpAddress target) {
            return target.family() == address.family()
                && target.numericValue().compareTo(network) >= 0
                && target.numericValue().compareTo(broadcast) <= 0;
        }

        String cidr() {
            return address.value() + "/" + prefix;
        }
    }

    static final class NetworkInterface {
        private final String name;
        private final IpAddress address;
        private final CidrNetwork subnet;
        private final int mtu;
        private InterfaceState state;

        NetworkInterface(
            String name,
            String cidr,
            int mtu
        ) {
            if (name == null || name.isBlank()) {
                throw new NetworkException("Interface name is required");
            }

            this.name = name;
            this.subnet = CidrNetwork.parse(cidr);
            this.address = subnet.address();
            this.mtu = mtu;
            this.state = InterfaceState.UP;

            if (mtu < 576 || mtu > 65535) {
                throw new NetworkException("Invalid MTU");
            }
        }

        String name() {
            return name;
        }

        IpAddress address() {
            return address;
        }

        CidrNetwork subnet() {
            return subnet;
        }

        int mtu() {
            return mtu;
        }

        InterfaceState state() {
            return state;
        }

        void setState(InterfaceState newState) {
            state = Objects.requireNonNull(newState);
        }
    }

    record Route(
        CidrNetwork destination,
        String interfaceName,
        Optional<IpAddress> nextHop,
        int metric,
        RouteState state
    ) {
        Route {
            Objects.requireNonNull(destination);
            Objects.requireNonNull(interfaceName);
            Objects.requireNonNull(nextHop);
            Objects.requireNonNull(state);

            if (metric < 0) {
                throw new NetworkException("Metric cannot be negative");
            }

            nextHop.ifPresent(gateway -> {
                if (gateway.family() != destination.address().family()) {
                    throw new NetworkException("Gateway family mismatch");
                }
            });
        }

        static Route create(
            String destination,
            String interfaceName,
            String nextHop,
            int metric
        ) {
            return new Route(
                CidrNetwork.parse(destination),
                interfaceName,
                Optional.ofNullable(nextHop)
                    .map(IpAddress::parse),
                metric,
                RouteState.ACTIVE
            );
        }
    }

    record ForwardingDecision(
        IpAddress source,
        IpAddress destination,
        IpAddress nextHop,
        String interfaceName,
        String matchedNetwork,
        int metric,
        String status
    ) {}

    interface RoutingPolicy {
        boolean accepts(Route route, NetworkInterface networkInterface);
    }

    static final class ActiveInterfacePolicy implements RoutingPolicy {
        @Override
        public boolean accepts(
            Route route,
            NetworkInterface networkInterface
        ) {
            return route.state() == RouteState.ACTIVE
                && networkInterface.state() == InterfaceState.UP
                && route.destination().address().family()
                    == networkInterface.address().family();
        }
    }

    static final class RouterService {

        private final Map<String, NetworkInterface> interfaces =
            new HashMap<>();

        private final List<Route> routes = new ArrayList<>();

        private final RoutingPolicy policy;

        RouterService(RoutingPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void addInterface(NetworkInterface networkInterface) {
            if (interfaces.containsKey(networkInterface.name())) {
                throw new NetworkException("Duplicate interface");
            }

            interfaces.put(
                networkInterface.name(),
                networkInterface
            );
        }

        void addRoute(Route route) {
            NetworkInterface outgoing =
                interfaces.get(route.interfaceName());

            if (outgoing == null) {
                throw new NetworkException("Unknown interface");
            }

            if (!policy.accepts(route, outgoing)) {
                throw new NetworkException(
                    "Interface or route is not eligible"
                );
            }

            route.nextHop().ifPresent(gateway -> {
                if (!outgoing.subnet().contains(gateway)) {
                    throw new NetworkException(
                        "Gateway is not reachable through outgoing subnet"
                    );
                }
            });

            routes.add(route);
        }

        Optional<Route> findRoute(IpAddress destination) {
            return routes.stream()
                .filter(route -> route.destination().contains(destination))
                .filter(route -> {
                    NetworkInterface outgoing =
                        interfaces.get(route.interfaceName());

                    return outgoing != null &&
                        policy.accepts(route, outgoing);
                })
                .sorted(
                    Comparator
                        .comparingInt(
                            (Route route) ->
                                route.destination().prefix()
                        )
                        .reversed()
                        .thenComparingInt(Route::metric)
                )
                .findFirst();
        }

        ForwardingDecision forward(
            String sourceText,
            String destinationText,
            int payloadBytes
        ) {
            IpAddress source = IpAddress.parse(sourceText);
            IpAddress destination = IpAddress.parse(destinationText);

            if (source.family() != destination.family()) {
                throw new NetworkException("Address family mismatch");
            }

            if (payloadBytes < 0) {
                throw new NetworkException("Negative payload size");
            }

            Route route = findRoute(destination)
                .orElseThrow(
                    () -> new NetworkException("No route available")
                );

            NetworkInterface outgoing =
                interfaces.get(route.interfaceName());

            int headerBytes = destination.family() ==
                AddressFamily.IPV4 ? 20 : 40;

            if (payloadBytes + headerBytes > outgoing.mtu()) {
                throw new NetworkException(
                    "Packet exceeds MTU; fragmentation is not simulated"
                );
            }

            return new ForwardingDecision(
                source,
                destination,
                route.nextHop().orElse(destination),
                outgoing.name(),
                route.destination().cidr(),
                route.metric(),
                "FORWARDED"
            );
        }

        void setInterfaceState(
            String name,
            InterfaceState state
        ) {
            NetworkInterface networkInterface = interfaces.get(name);

            if (networkInterface == null) {
                throw new NetworkException("Unknown interface");
            }

            networkInterface.setState(state);
        }

        void printRoutingTable() {
            System.out.println("\nROUTING TABLE");

            routes.stream()
                .sorted(
                    Comparator.comparingInt(
                        (Route route) ->
                            route.destination().prefix()
                    ).reversed()
                )
                .forEach(route -> System.out.printf(
                    "%-24s %-20s %-10s metric=%d%n",
                    route.destination().cidr(),
                    route.nextHop()
                        .map(IpAddress::value)
                        .orElse("DIRECT"),
                    route.interfaceName(),
                    route.metric()
                ));
        }

        void printInterfaces() {
            System.out.println("\nINTERFACES");

            interfaces.values().forEach(networkInterface ->
                System.out.printf(
                    "%s %s %s MTU=%d STATE=%s%n",
                    networkInterface.name(),
                    networkInterface.address().value(),
                    networkInterface.subnet().cidr(),
                    networkInterface.mtu(),
                    networkInterface.state()
                )
            );
        }
    }

    static void analyzeSubnet(String cidr) {
        CidrNetwork network = CidrNetwork.parse(cidr);

        System.out.println("\nSUBNET ANALYSIS");
        System.out.println("Network: " + network.cidr());
        System.out.println("Family: " + network.address().family());
        System.out.println("Prefix: " + network.prefix());
        System.out.println("Total addresses: " +
            network.totalAddresses());

        System.out.println("Network numeric value: " +
            network.network());

        System.out.println("Last address numeric value: " +
            network.broadcast());

        if (network.address().family() == AddressFamily.IPV4) {
            System.out.println("Broadcast: " +
                network.broadcast());
        }
    }

    static List<CidrNetwork> divideSubnet(
        String cidr,
        int newPrefix
    ) {
        CidrNetwork parent = CidrNetwork.parse(cidr);

        if (newPrefix < parent.prefix() ||
            newPrefix > parent.address().family().bits()) {
            throw new NetworkException("Invalid child prefix");
        }

        BigInteger count = BigInteger.ONE.shiftLeft(
            newPrefix - parent.prefix()
        );

        if (count.compareTo(BigInteger.valueOf(4096)) > 0) {
            throw new NetworkException("Too many child networks");
        }

        BigInteger childSize = BigInteger.ONE.shiftLeft(
            parent.address().family().bits() - newPrefix
        );

        List<CidrNetwork> result = new ArrayList<>();

        for (int index = 0; index < count.intValue(); index++) {
            BigInteger start = parent.network().add(
                childSize.multiply(BigInteger.valueOf(index))
            );

            result.add(new CidrNetwork(
                new IpAddress(
                    start.toString(),
                    parent.address().family(),
                    start
                ),
                newPrefix,
                start,
                start.add(childSize).subtract(BigInteger.ONE),
                BigInteger.ONE.shiftLeft(
                    parent.address().family().bits()
                ).subtract(BigInteger.ONE)
                    .shiftRight(
                        parent.address().family().bits() - newPrefix
                    )
                    .shiftLeft(
                        parent.address().family().bits() - newPrefix
                    )
            ));
        }

        return result;
    }

    public static void main(String[] args) {
        try {
            System.out.println("NETWORK LAYER ENGINEERING");

            analyzeSubnet("192.168.10.0/24");
            analyzeSubnet("2001:db8:1::/64");

            System.out.println("\nSUBNET DIVISION");

            divideSubnet("192.168.10.0/24", 26)
                .forEach(network ->
                    System.out.println(network.cidr())
                );

            RouterService router = new RouterService(
                new ActiveInterfacePolicy()
            );

            router.addInterface(
                new NetworkInterface(
                    "eth0",
                    "192.168.10.1/24",
                    1500
                )
            );

            router.addInterface(
                new NetworkInterface(
                    "eth1",
                    "10.0.0.1/24",
                    1500
                )
            );

            router.addInterface(
                new NetworkInterface(
                    "eth2",
                    "2001:db8:1::1/64",
                    1500
                )
            );

            router.addRoute(
                Route.create(
                    "0.0.0.0/0",
                    "eth1",
                    "10.0.0.254",
                    200
                )
            );

            router.addRoute(
                Route.create(
                    "172.16.0.0/16",
                    "eth1",
                    "10.0.0.2",
                    50
                )
            );

            router.addRoute(
                Route.create(
                    "172.16.10.0/24",
                    "eth1",
                    "10.0.0.3",
                    10
                )
            );

            router.addRoute(
                Route.create(
                    "2001:db8:2::/64",
                    "eth2",
                    "2001:db8:1::2",
                    100
                )
            );

            router.printInterfaces();
            router.printRoutingTable();

            System.out.println("\nIPV4 PACKET FORWARDING");

            ForwardingDecision ipv4 = router.forward(
                "192.168.10.20",
                "172.16.10.50",
                1200
            );

            System.out.println(ipv4);

            if (!ipv4.matchedNetwork().equals("172.16.10.0/24")) {
                throw new NetworkException(
                    "Longest-prefix matching failed"
                );
            }

            System.out.println("\nIPV6 PACKET FORWARDING");

            System.out.println(
                router.forward(
                    "2001:db8:1::10",
                    "2001:db8:2::20",
                    1200
                )
            );

            System.out.println("\nFAILURE TESTS");

            try {
                IpAddress.parse("192.168.1.999");
            } catch (NetworkException exception) {
                System.out.println(exception.getMessage());
            }

            try {
                router.forward(
                    "192.168.10.20",
                    "203.0.113.10",
                    100
                );
            } catch (NetworkException exception) {
                System.out.println(
                    "Expected failure: " + exception.getMessage()
                );
            }

            try {
                router.forward(
                    "192.168.10.20",
                    "172.16.10.50",
                    2000
                );
            } catch (NetworkException exception) {
                System.out.println(
                    "Expected MTU failure: " + exception.getMessage()
                );
            }

            router.setInterfaceState("eth1", InterfaceState.DOWN);

            try {
                router.forward(
                    "192.168.10.20",
                    "172.16.10.50",
                    100
                );
            } catch (NetworkException exception) {
                System.out.println(
                    "Expected interface failure: " + exception.getMessage()
                );
            }

            System.out.println("\nNETWORK TESTS COMPLETED");

        } catch (Exception exception) {
            System.err.println(
                "NETWORK ERROR: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
