import ReactMarkdown from "react-markdown";
import matter from "gray-matter";
import { readReadme } from "@/lib/repo";

export async function DocsContent() {
  const readme = await readReadme();
  const { content } = matter(readme);

  return (
    <article className="prose prose-invert max-w-none prose-headings:text-white prose-strong:text-white prose-a:text-primary">
      <ReactMarkdown>{content}</ReactMarkdown>
    </article>
  );
}
