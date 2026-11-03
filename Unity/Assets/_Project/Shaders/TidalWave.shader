Shader "Planet/TidalWave"
{
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
        Cull Off
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            struct A { float3 p:POSITION; half4 c:COLOR; float3 n:NORMAL; };
            struct V { float4 p:SV_POSITION; half4 c:COLOR; float3 n:TEXCOORD0;float fog:TEXCOORD1;float3 w:TEXCOORD2; };
            V Vert(A i) { V o; o.w=TransformObjectToWorld(i.p);o.p=TransformWorldToHClip(o.w);o.c=i.c;o.n=TransformObjectToWorldNormal(i.n);o.fog=ComputeFogFactor(o.p.z);return o; }
            half4 Frag(V i):SV_Target
            {
                Light sun=GetMainLight();float l=.6+.4*abs(dot(normalize(i.n),sun.direction));
                float shimmer=.97+.03*sin(i.w.x*.9+_Time.y*3+i.w.y*.8);
                return half4(MixFog(i.c.rgb*l*shimmer,i.fog),1);
            }
            ENDHLSL
        }
    }
}
