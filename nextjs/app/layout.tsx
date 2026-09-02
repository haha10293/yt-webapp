export const metadata = {
	title: "web Video Downloader",
	description: "Simple downloader",
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="ja">
		<body>{children}</body>
		</html>
	);
}
